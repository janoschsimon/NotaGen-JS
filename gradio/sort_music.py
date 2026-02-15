import os
import shutil

# Definiere die Kategorien
categories = ["Chamber", "Orchestra", "Art Song", "Vocal-Orchestral", "Keyboard", "Choral"]

# Hol das aktuelle Verzeichnis
current_dir = os.getcwd()

# Stelle sicher, dass die Ordner existieren
for category in categories:
    os.makedirs(os.path.join(current_dir, category), exist_ok=True)

# Durch alle Dateien im Verzeichnis gehen
for file in os.listdir(current_dir):
    if file.endswith(".xml") or file.endswith(".abc"):
        # Checken, ob eine der Kategorien im Dateinamen vorkommt
        for category in categories:
            if category in file:
                src_path = os.path.join(current_dir, file)
                dest_path = os.path.join(current_dir, category, file)
                shutil.move(src_path, dest_path)
                print(f"Verschoben: {file} → {category}/")
                break  # Sobald eine Kategorie gefunden wurde, abbrechen

print("✅ Sortierung abgeschlossen!")
