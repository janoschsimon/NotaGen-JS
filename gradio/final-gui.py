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
import config  # Importiere config, um Parameter dynamisch zu setzen

# Predefined valid combinations set
with open('prompts.txt', 'r') as f:
    prompts = f.readlines()
valid_combinations = set()
for prompt in prompts:
    prompt = prompt.strip()
    parts = prompt.split('_')
    valid_combinations.add((parts[0], parts[1], parts[2]))

# Generate available options
periods = sorted({p for p, _, _ in valid_combinations})
composers = sorted({c for _, c, _ in valid_combinations})
instruments = sorted({i for _, _, i in valid_combinations})

# Dynamic component updates
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


class RealtimeStream(TextIOBase):
    def __init__(self, queue):
        self.queue = queue
    
    def write(self, text):
        self.queue.put(text)
        return len(text)


def save_and_convert(abc_content, period, composer, instrumentation):
    if not all([period, composer, instrumentation]):
        raise gr.Error("Please complete a valid generation first before saving")
    
    import os
    import time
    
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
        raise gr.Error(f"ABC zu XML Konvertierung fehlgeschlagen: {error_msg}. Bitte versuchen Sie eine andere Komposition zu generieren.")
    
    finally:
        # Versuche die temporäre ABC-Datei zu löschen, aber ignoriere Fehler
        try:
            time.sleep(0.5)
            if os.path.exists(temp_abc_filename):
                os.remove(temp_abc_filename)
        except Exception:
            pass


def generate_music(period, composer, instrumentation):
    if (period, composer, instrumentation) not in valid_combinations:
        raise gr.Error("Invalid prompt combination! Please re-select from the period options")
    
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
            yield process_output, None, ""  # Leerer String für save_status während der Generierung
        except queue.Empty:
            continue
    
    while not output_queue.empty():
        text = output_queue.get()
        process_output += text
        yield process_output, None, ""  # Leerer String für save_status während der Generierung
    
    final_result = result_container[0] if result_container else ""
    
    # Automatisch speichern, sobald die Generierung abgeschlossen ist
    save_status = ""
    if final_result and all([period, composer, instrumentation]):
        try:
            save_status = save_and_convert(final_result, period, composer, instrumentation)
        except Exception as e:
            save_status = f"Fehler beim Speichern: {str(e)}"
    else:
        save_status = "Konnte nicht automatisch speichern. Ungültige Generierung."
    
    # Endgültiges Ergebnis mit Speicherstatus zurückgeben
    yield process_output, final_result, save_status


def batch_generate_music(period, composer, instrumentation, batch_count, top_k, top_p, temperature, patch_length):
    # Setze dynamisch die Parameter in config
    config.TOP_K = top_k
    config.TOP_P = top_p
    config.TEMPERATURE = temperature
    config.PATCH_LENGTH = patch_length
    
    if (period, composer, instrumentation) not in valid_combinations:
        raise gr.Error("Invalid prompt combination! Please re-select from the period options")
    
    for batch_index in range(batch_count):
        batch_info = f"\n\n--- BATCH GENERATION {batch_index + 1}/{batch_count} ---\n\n"
        process_output = batch_info
        yield process_output, None, f"Starte Batch-Generation {batch_index + 1}/{batch_count}..."
        generator = generate_music(period, composer, instrumentation)
        last_output = None
        for output in generator:
            process_output = batch_info + output[0]
            final_result = output[1]
            save_status = output[2]
            yield process_output, final_result, save_status
            last_output = output
        time.sleep(1)
    final_process_output = last_output[0] + "\n\n--- BATCH GENERATION ABGESCHLOSSEN ---"
    yield final_process_output, last_output[1], f"Batch-Generation abgeschlossen: {batch_count} Stücke generiert"


with gr.Blocks() as demo:
    gr.Markdown("## NotaGen")
    
    with gr.Row():
        # Linke Spalte
        with gr.Column():
            period_dd = gr.Dropdown(
                choices=periods,
                value=None, 
                label="Period",
                interactive=True
            )
            composer_dd = gr.Dropdown(
                choices=[],
                value=None,
                label="Composer",
                interactive=False
            )
            instrument_dd = gr.Dropdown(
                choices=[],
                value=None,
                label="Instrumentation",
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
            
            # Parameter Einstellungen als Slider in einem Accordion
            with gr.Accordion("Parameter Einstellungen", open=False):
                top_k_slider = gr.Slider(
                    minimum=1,
                    maximum=100,
                    value=config.TOP_K,
                    step=1,
                    label="Top K (Sampling)"
                )
                top_p_slider = gr.Slider(
                    minimum=0.1,
                    maximum=1.0,
                    value=config.TOP_P,
                    step=0.05,
                    label="Top P (Sampling)"
                )
                temperature_slider = gr.Slider(
                    minimum=0.5,
                    maximum=2.0,
                    value=config.TEMPERATURE,
                    step=0.1,
                    label="Temperature (Sampling)"
                )
                patch_length_slider = gr.Slider(
                    minimum=256,
                    maximum=2048,
                    value=config.PATCH_LENGTH,
                    step=256,
                    label="Patch Length"
                )
            
            generate_btn = gr.Button("Generate!", variant="primary")
            
            process_output = gr.Textbox(
                label="Generation process",
                interactive=False,
                lines=15,
                max_lines=15,
                placeholder="Generation progress will be shown here...",
                elem_classes="process-output"
            )

        # Rechte Spalte
        with gr.Column():
            final_output = gr.Textbox(
                label="Post-processed ABC notation scores",
                interactive=True,
                lines=23,
                placeholder="Post-processed ABC scores will be shown here...",
                elem_classes="final-output"
            )
            
            save_status = gr.Textbox(
                label="Save Status",
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
        batch_generate_music,  # Geändert von generate_music zu batch_generate_music
        inputs=[period_dd, composer_dd, instrument_dd, batch_slider, top_k_slider, top_p_slider, temperature_slider, patch_length_slider],
        outputs=[process_output, final_output, save_status]
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
"""

demo.css = css

if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=7861,
        share=True  # Aktiviert öffentlichen Link
    )
