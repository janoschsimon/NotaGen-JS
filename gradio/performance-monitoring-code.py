import gradio as gr
import sys
import threading
import queue
from io import TextIOBase
from inference import inference_patch
import datetime
import subprocess
import os
import tempfile
import time
import torch  # Import für VRAM-Optimierung
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# Klasse für die Leistungsüberwachung
class PerformanceMonitor:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.generation_times = []
        self.iteration_times = []
        self.iteration_counts = []
        self.it_per_sec = []
        self.current_it_sec = 0
        self.total_iterations = 0
        self.last_iteration_time = None
        
    def start_generation(self):
        """Startet die Zeitmessung für eine neue Generierung"""
        self.start_time = time.time()
        self.last_iteration_time = self.start_time
        self.iteration_times = []
        self.it_per_sec = []
        self.total_iterations = 0
        
    def log_iteration(self):
        """Zeichnet eine neue Iteration auf"""
        current_time = time.time()
        
        # Zeit seit der letzten Iteration berechnen
        if self.last_iteration_time:
            time_diff = current_time - self.last_iteration_time
            if time_diff > 0:  # Verhindere Division durch Null
                it_sec = 1.0 / time_diff
                self.it_per_sec.append(it_sec)
                self.current_it_sec = it_sec
        
        self.last_iteration_time = current_time
        self.total_iterations += 1
        self.iteration_times.append(current_time - self.start_time)
        self.iteration_counts.append(self.total_iterations)
        
    def finish_generation(self):
        """Beendet die Zeitmessung für die aktuelle Generierung"""
        self.end_time = time.time()
        total_time = self.end_time - self.start_time
        self.generation_times.append(total_time)
        return total_time
    
    def get_avg_it_sec(self):
        """Berechnet die durchschnittliche Anzahl von Iterationen pro Sekunde"""
        if not self.it_per_sec:
            return 0
        return sum(self.it_per_sec) / len(self.it_per_sec)
    
    def get_current_it_sec(self):
        """Gibt die aktuelle Iterationsrate zurück"""
        return self.current_it_sec
    
    def plot_performance(self, piece_name, output_dir="performance_plots"):
        """Erstellt und speichert Leistungsgrafiken"""
        if not self.iteration_times:
            return None
            
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Bereinige den Dateinamen
        safe_name = ''.join(c if c.isalnum() or c in '_- ' else '_' for c in piece_name)
        filename = f"{timestamp}_{safe_name}_performance.png"
        filepath = os.path.join(output_dir, filename)
        
        # Erstelle die Grafik
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Plot für kumulierte Iterationen über Zeit
        ax1.plot(self.iteration_times, self.iteration_counts, 'b-')
        ax1.set_xlabel('Zeit (Sekunden)')
        ax1.set_ylabel('Iterationen')
        ax1.set_title(f'Iterationsverlauf: {piece_name}')
        ax1.grid(True)
        
        # Plot für it/sec über Zeit
        if len(self.iteration_times) > 1:
            # Berechne it/sec für jeden Zeitpunkt
            times = self.iteration_times[1:]
            diffs = np.diff(self.iteration_times)
            rates = 1.0 / diffs
            
            ax2.plot(times, rates, 'r-')
            ax2.set_xlabel('Zeit (Sekunden)')
            ax2.set_ylabel('Iterationen pro Sekunde')
            ax2.set_title('Generierungsgeschwindigkeit')
            ax2.grid(True)
        
        plt.tight_layout()
        plt.savefig(filepath)
        plt.close(fig)
        
        return filepath

# Globale Instanz des Performance Monitors
perf_monitor = PerformanceMonitor()

# VRAM-Optimierung: Funktion zum Leeren des CUDA-Caches
def clear_gpu_memory():
    """Leert den PyTorch CUDA-Cache, um VRAM freizugeben"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        return "CUDA-Cache geleert"
    return "Kein CUDA verfügbar"

# Klasse für die Echtzeit-Textausgabe
class RealtimeStream(TextIOBase):
    def __init__(self, queue):
        self.queue = queue
    
    def write(self, text):
        self.queue.put(text)
        # Wir nehmen an, dass jede neue Zeile eine neue Iteration darstellt
        if '\n' in text:
            perf_monitor.log_iteration()
        return len(text)


def save_and_convert(abc_content, period, composer, instrumentation):
    if not all([period, composer, instrumentation]):
        raise gr.Error("Bitte führen Sie zuerst eine gültige Generierung durch")
    
    # Formatiere den Komponistennamen (von "Nachname, Vorname" zu "Vorname_Nachname") für den Ordnerpfad
    if "," in composer:
        last_name, first_name = composer.split(",", 1)
        composer_formatted = f"{first_name.strip()}_{last_name.strip()}"
    else:
        composer_formatted = composer.replace(" ", "_")
    
    # Erstelle Verzeichnisstruktur: Epoche/Komponist/Instrument
    output_dir = os.path.join(period, composer_formatted, instrumentation)
    os.makedirs(output_dir, exist_ok=True)
    
    # Zeitstempel für den Dateinamen
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Original Dateiname im Format YYYYMMDD_HHMMSS_Period_Composer_Instrumentation.xml
    original_filename = f"{timestamp}_{period}_{composer}_{instrumentation}.xml"
    
    # Erzeuge eine temporäre ABC-Datei im aktuellen Verzeichnis
    temp_abc_filename = f"temp_{timestamp}.abc"
    
    try:
        # Schreibe den Inhalt in die temporäre Datei
        with open(temp_abc_filename, "w", encoding="utf-8") as f:
            f.write(abc_content)
        
        # Der endgültige XML-Dateiname im Zielverzeichnis
        xml_filename = os.path.join(output_dir, original_filename)
        
        # Konvertiere von ABC zu XML
        result = subprocess.run(
            ["python", "abc2xml.py", '-o', '.', temp_abc_filename],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Das abc2xml-Tool erstellt die XML-Datei im selben Verzeichnis
        temp_xml_filename = os.path.splitext(temp_abc_filename)[0] + '.xml'
        
        # Prüfen ob die XML-Datei existiert
        if os.path.exists(temp_xml_filename):
            # Umbenennen und Verschieben der XML-Datei
            if os.path.exists(xml_filename):
                os.remove(xml_filename)
            os.rename(temp_xml_filename, xml_filename)
            return f"Erfolgreich gespeichert: {xml_filename}"
        else:
            # Wenn die erwartete XML-Datei nicht gefunden wurde
            # Suche nach anderen XML-Dateien im aktuellen Verzeichnis
            all_files = os.listdir('.')
            xml_files = [f for f in all_files if f.endswith('.xml') and f.startswith('temp_')]
            
            if xml_files:
                # Verwende die erste gefundene passende XML-Datei
                found_xml = xml_files[0]
                if os.path.exists(xml_filename):
                    os.remove(xml_filename)
                os.rename(found_xml, xml_filename)
                return f"Erfolgreich gespeichert: {xml_filename}"
            else:
                return f"Fehler: Keine XML-Datei wurde erstellt. Überprüfen Sie die Konvertierung."
    
    except subprocess.CalledProcessError as e:
        error_msg = f"Konvertierung fehlgeschlagen: {e.stderr}" if e.stderr else "Unbekannter Fehler"
        raise gr.Error(f"ABC zu XML Konvertierung fehlgeschlagen: {error_msg}")
    
    finally:
        # Versuche die temporäre ABC-Datei zu löschen, aber ignoriere Fehler
        try:
            time.sleep(0.5)
            if os.path.exists(temp_abc_filename):
                os.remove(temp_abc_filename)
        except Exception:
            pass


def generate_music(period, composer, instrumentation):
    if not all([period, composer, instrumentation]):
        raise gr.Error("Bitte wählen Sie Epoche, Komponist und Instrumentierung aus")
    
    # VRAM-Optimierung: Cache zu Beginn leeren
    clear_gpu_memory()
    
    # Performance-Überwachung starten
    perf_monitor.start_generation()
    
    output_queue = queue.Queue()
    original_stdout = sys.stdout
    sys.stdout = RealtimeStream(output_queue)
    
    result_container = []
    
    def run_inference():
        try:
            result_container.append(inference_patch(period, composer, instrumentation))
        finally:
            sys.stdout = original_stdout
    
    thread = threading.Thread(target=run_inference)
    thread.start()
    
    process_output = ""
    while thread.is_alive():
        try:
            text = output_queue.get(timeout=0.1)
            process_output += text
            
            # Leistungsmetriken aktualisieren
            current_it_sec = perf_monitor.get_current_it_sec()
            
            yield (
                process_output, 
                None, 
                "", 
                "Generiere...", 
                f"{period} - {composer} - {instrumentation}",
                f"{current_it_sec:.2f} it/sec"
            )
        except queue.Empty:
            continue
    
    while not output_queue.empty():
        text = output_queue.get()
        process_output += text
        
        # Letzte Leistungsmetriken aktualisieren
        current_it_sec = perf_monitor.get_current_it_sec()
        
        yield (
            process_output, 
            None, 
            "", 
            "Generiere...", 
            f"{period} - {composer} - {instrumentation}",
            f"{current_it_sec:.2f} it/sec"
        )
    
    # Abschluss der Generierung in der Leistungsüberwachung
    total_gen_time = perf_monitor.finish_generation()
    avg_it_sec = perf_monitor.get_avg_it_sec()
    
    # Erstelle und speichere Performance-Plot
    piece_name = f"{period}_{composer}_{instrumentation}"
    perf_plot_path = perf_monitor.plot_performance(piece_name)
    
    final_result = result_container[0] if result_container else ""
    
    # VRAM-Optimierung: Nach der Generierung Cache leeren
    clear_gpu_memory()
    
    # Automatisch speichern, sobald die Generierung abgeschlossen ist
    save_status = ""
    if final_result and all([period, composer, instrumentation]):
        try:
            save_status = save_and_convert(final_result, period, composer, instrumentation)
            if perf_plot_path:
                save_status += f"\nPerformance-Plot gespeichert: {perf_plot_path}"
        except Exception as e:
            save_status = f"Fehler beim Speichern: {str(e)}"
    else:
        save_status = "Konnte nicht automatisch speichern. Ungültige Generierung."
    
    # VRAM-Optimierung: Nach dem Speichern nochmals Cache leeren
    clear_gpu_memory()
    
    # Füge Performance-Zusammenfassung zum Prozess-Output hinzu
    performance_summary = f"\n\n--- PERFORMANCE SUMMARY ---\n"
    performance_summary += f"Gesamtzeit: {total_gen_time:.2f} Sekunden\n"
    performance_summary += f"Durchschnitt: {avg_it_sec:.2f} it/sec\n"
    performance_summary += f"Gesamt-Iterationen: {perf_monitor.total_iterations}\n"
    process_output += performance_summary
    
    # Endgültiges Ergebnis mit Speicherstatus zurückgeben
    yield (
        process_output, 
        final_result, 
        save_status, 
        "Abgeschlossen", 
        f"{period} - {composer} - {instrumentation}",
        f"Ø {avg_it_sec:.2f} it/sec, Gesamtzeit: {total_gen_time:.2f}s"
    )


def batch_generate_music(period, composer, instrumentation, batch_count):
    """
    Generiert mehrere Musikstücke nacheinander in einem Batch-Prozess.
    """
    if not all([period, composer, instrumentation]):
        raise gr.Error("Bitte wählen Sie Epoche, Komponist und Instrumentierung aus")
    
    # VRAM-Optimierung: Zu Beginn des Batch-Prozesses Cache leeren
    clear_gpu_memory()
    
    all_performance_data = []
    
    for batch_index in range(batch_count):
        # VRAM-Optimierung: Vor jeder neuen Generierung Cache leeren
        clear_gpu_memory()
        
        # Aktualisiere den Batch-Fortschritt in der GUI
        batch_progress = f"Batch {batch_index + 1} von {batch_count}"
        current_piece = f"{period} - {composer} - {instrumentation}"
        
        batch_info = f"\n\n--- BATCH GENERATION {batch_index + 1}/{batch_count} ---\n\n"
        
        # Informiere den Benutzer über den Beginn einer neuen Batch-Generation
        process_output = batch_info
        yield (
            process_output, 
            None, 
            f"Starte Batch-Generation {batch_index + 1}/{batch_count}...", 
            batch_progress, 
            current_piece,
            "Initialisiere..."
        )
        
        # Generierungs-Generator erstellen
        generator = generate_music(period, composer, instrumentation)
        
        # Extrahiere Ergebnisse vom Generator
        last_output = None
        for output in generator:
            # Format der Ausgabe: (process_output, final_result, save_status, batch_progress, current_piece, perf_metrics)
            process_output = batch_info + output[0]
            final_result = output[1]
            save_status = output[2]
            perf_metrics = output[5]
            
            yield (
                process_output, 
                final_result, 
                save_status, 
                batch_progress, 
                current_piece, 
                perf_metrics
            )
            last_output = output
        
        # Sammle Leistungsdaten für den Vergleich
        if last_output:
            all_performance_data.append({
                'batch': batch_index + 1,
                'avg_it_sec': perf_monitor.get_avg_it_sec(),
                'total_time': perf_monitor.generation_times[-1] if perf_monitor.generation_times else 0
            })
        
        # VRAM-Optimierung: Nach der Generierung nochmals Cache leeren
        clear_gpu_memory()
        
        # Kurze Pause zwischen den Generationen
        time.sleep(1)
    
    # Erstelle Batch-Vergleichsdiagramm
    if all_performance_data:
        # Erstelle den Plot-Ordner, falls er nicht existiert
        plot_dir = "performance_plots"
        os.makedirs(plot_dir, exist_ok=True)
        
        # Extrahiere Daten für den Plot
        batch_nums = [data['batch'] for data in all_performance_data]
        it_secs = [data['avg_it_sec'] for data in all_performance_data]
        total_times = [data['total_time'] for data in all_performance_data]
        
        # Erstelle den Plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        ax1.bar(batch_nums, it_secs, color='blue')
        ax1.set_xlabel('Batch-Nummer')
        ax1.set_ylabel('Durchschnittliche it/sec')
        ax1.set_title('Leistungsvergleich zwischen Batches (Geschwindigkeit)')
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        ax2.bar(batch_nums, total_times, color='green')
        ax2.set_xlabel('Batch-Nummer')
        ax2.set_ylabel('Gesamtzeit (s)')
        ax2.set_title('Leistungsvergleich zwischen Batches (Dauer)')
        ax2.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        
        # Speichere den Plot
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_plot_path = os.path.join(plot_dir, f"{timestamp}_batch_comparison.png")
        plt.savefig(batch_plot_path)
        plt.close(fig)
        
        # Batch-Statistiken
        avg_batch_time = sum(total_times) / len(total_times)
        avg_batch_speed = sum(it_secs) / len(it_secs)
        stats_summary = f"\n\n--- BATCH PERFORMANCE SUMMARY ---\n"
        stats_summary += f"Durchschnittszeit pro Batch: {avg_batch_time:.2f} Sekunden\n"
        stats_summary += f"Durchschnittsgeschwindigkeit: {avg_batch_speed:.2f} it/sec\n"
        stats_summary += f"Vergleichsdiagramm gespeichert: {batch_plot_path}"
    else:
        stats_summary = "\n\nKeine Performance-Daten verfügbar."
    
    # Batch-Abschluss Nachricht
    final_process_output = last_output[0] + "\n\n--- BATCH GENERATION ABGESCHLOSSEN ---" + stats_summary
    
    # VRAM-Optimierung: Am Ende des gesamten Batch-Prozesses Cache leeren
    clear_gpu_memory()
    
    yield (
        final_process_output, 
        last_output[1], 
        f"Batch-Generation abgeschlossen: {batch_count} Stücke generiert", 
        "Abgeschlossen", 
        "Alle Stücke generiert",
        f"Durchschnitt: {avg_batch_speed:.2f} it/sec, Gesamtzeit: {sum(total_times):.2f}s"
    )


# Definiere die verfügbaren gültigen Kombinationen aus der prompts.txt-Datei
with open('prompts.txt', 'r') as f:
    prompts = f.readlines()

valid_combinations = set()
for prompt in prompts:
    prompt = prompt.strip()
    parts = prompt.split('_')
    if len(parts) >= 3:
        valid_combinations.add((parts[0], parts[1], parts[2]))

# Extrahiere die verfügbaren Optionen
periods = sorted({p for p, _, _ in valid_combinations})
composers = sorted({c for _, c, _ in valid_combinations})
instruments = sorted({i for _, _, i in valid_combinations})


# Dynamische Komponentenaktualisierung
def update_components(period, composer):
    if not period:
        return [
            gr.Dropdown(choices=[], value=None, interactive=False),
            gr.Dropdown(choices=[], value=None, interactive=False)
        ]
    
    valid_composers = sorted({c for p, c, _ in valid_combinations if p == period})
    valid_instruments = sorted({i for p, c, i in valid_combinations if p == period and c == composer}) if composer else []
    
    return [
        gr.Dropdown(
            choices=valid_composers,
            value=composer if composer in valid_composers else None,
            interactive=True  
        ),
        gr.Dropdown(
            choices=valid_instruments,
            value=None,
            interactive=bool(valid_instruments)  
        )
    ]


# Erstelle die Gradio-Benutzeroberfläche
with gr.Blocks() as demo:
    gr.Markdown("## NotaGen mit Leistungsüberwachung")
    
    with gr.Row():
        # Linke Spalte
        with gr.Column():
            period_dd = gr.Dropdown(
                choices=periods,
                value=None, 
                label="Epoche",
                interactive=True
            )
            composer_dd = gr.Dropdown(
                choices=[],
                value=None,
                label="Komponist",
                interactive=False
            )
            instrument_dd = gr.Dropdown(
                choices=[],
                value=None,
                label="Instrumentierung",
                interactive=False
            )
            
            # Batch-Generation Slider
            batch_slider = gr.Slider(
                minimum=1,
                maximum=10,
                value=1,
                step=1,
                label="Anzahl der zu generierenden Stücke",
                interactive=True
            )
            
            # Batch-Fortschrittsanzeige und Performance-Metriken
            with gr.Row():
                batch_progress = gr.Textbox(
                    label="Batch-Fortschritt",
                    value="Bereit",
                    interactive=False,
                    elem_classes="batch-progress"
                )
                current_piece = gr.Textbox(
                    label="Aktuelles Stück",
                    value="Keins ausgewählt",
                    interactive=False,
                    elem_classes="current-piece"
                )
            
            # Performance-Metriken
            perf_metrics = gr.Textbox(
                label="Leistungsmetriken",
                value="0.00 it/sec",
                interactive=False,
                elem_classes="perf-metrics"
            )
            
            generate_btn = gr.Button("Generate!", variant="primary")
            
            process_output = gr.Textbox(
                label="Generierungsprozess",
                interactive=False,
                lines=15,
                max_lines=15,
                placeholder="Generierungsfortschritt wird hier angezeigt...",
                elem_classes="process-output"
            )

        # Rechte Spalte
        with gr.Column():
            final_output = gr.Textbox(
                label="Nachbearbeitete ABC-Notation",
                interactive=True,
                lines=23,
                placeholder="Nachbearbeitete ABC-Notation wird hier angezeigt...",
                elem_classes="final-output"
            )
            
            save_status = gr.Textbox(
                label="Speicherstatus",
                interactive=False,
                visible=True,
                max_lines=2
            )
    
    period_dd.change(
        update_components,
        inputs=[period_dd, composer_dd],
        outputs=[composer_dd, instrument_dd]
    )
    composer_dd.change(
        update_components,
        inputs=[period_dd, composer_dd],
        outputs=[composer_dd, instrument_dd]
    )
    
    generate_btn.click(
        batch_generate_music,
        inputs=[period_dd, composer_dd, instrument_dd, batch_slider],
        outputs=[process_output, final_output, save_status, batch_progress, current_piece, perf_metrics]
    )


css = """
.process-output {
    background-color: #f0f0f0;
    font-family: monospace;
    padding: 10px;
    border-radius: 5px;
}

.final-output {
    background-color: #ffffff;
    font-family: sans-serif;
    padding: 10px;
    border-radius: 5px;
}

.process-output textarea {
    max-height: 500px !important;
    overflow-y: auto !important;
    white-space: pre-wrap;
}

.batch-progress, .current-piece, .perf-metrics {
    background-color: #e6f7ff;
    border: 1px solid #91d5ff;
    border-radius: 5px;
    padding: 5px;
    text-align: center;
    font-weight: bold;
}

.batch-progress {
    color: #0050b3;
}

.current-piece {
    color: #006d75;
}

.perf-metrics {
    color: #d4380d;
    background-color: #fff2e8;
    border-color: #ffbb96;
}
"""

demo.css = css

if __name__ == "__main__":
    # VRAM-Optimierung: Beim Start Cache leeren
    clear_gpu_memory()
    
    demo.launch(
        server_name="127.0.0.1",
        server_port=7861,
        share=True  # Aktiviert öffentlichen Link
    )
