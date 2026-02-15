# Session 2026-02-15 - Setup & Upstream Merge

## Was gemacht wurde

### Git Setup
- Upstream ElectricAlexis/NotaGen gemergt (24 Commits hinter)
- Remotes umgebaut: `origin` = janoschsimon/NotaGen-JS, `upstream` = ElectricAlexis/NotaGen
- Backup-Branch erstellt: `backup-before-merge-feb2026`
- `.gitignore` angelegt (Weights, Trainingsdaten, persönliche Ordner excluded)
- Alles gepusht auf https://github.com/janoschsimon/NotaGen-JS

### Wichtige Änderungen durch Upstream-Merge
- `gradio/inference.py`: Jetzt mit `torch.inference_mode()` + `torch.autocast(fp16)` → schneller!
- `gradio/inference.py`: `prepare_model_for_kbit_training()` hinzugekommen
- `notebook/abc2xml.py` + `notebook/demo.ipynb` neu
- Alle `utils.py` files geupdated (numpy probability fix)

### Eigene Files auf GitHub
- `gradio/final-gui.py` - Haupt-GUI
- `gradio/x_notagen-vram-optimized.py` - VRAM-Version
- `gradio/sort_music.py`, `performance-monitoring-code.py`, `data/mxltoxml.py`
- `NOTAGEN_WINDOWS_GUIDE.md`, `CLAUDE.md`

---

## Training Pipeline - Vollständige Anleitung

### Welche Weights brauchen wir? (DIE wichtigste Frage!)

Es gibt 3 Modell-Varianten bei NotaGen:
- `NotaGen-small` / `NotaGen-medium` / `NotaGen-large` → **NICHT für uns!**
  - Haben KEINE Period/Composer/Instrumentation Konditionierung
  - Generieren "gibberish" bei Prompts
  - Nur für Pretraining von Grund auf
- **`NotaGen-X`** → **DAS ist unser Modell!** ✅
  - RL-optimiert (DeepSeek-R1 Ansatz)
  - Hat Period/Composer/Instrumentation Konditionierung
  - Funktioniert mit Gradio-UI Dropdowns
  - Weights: `weights_notagenx_p_size_16_p_length_1024_p_layers_20_h_size_1280.pth`

**→ Wir brauchen NUR NotaGen-X Weights. Die anderen 3 sind irrelevant für uns.**

### VRAM Anforderungen
| Task | VRAM | Hardware |
|------|------|----------|
| Inference (Musik generieren) | 24GB | 4090 ✅ lokal |
| Fine-tuning NotaGen-X | 40GB+ | RunPod A100 |
| Fine-tuning NotaGen-Large | >40GB | H800 (Autoren) |

### Komplette Training Pipeline

```
SCHRITT 1: Daten sammeln
- ~100 Stücke MusicXML (IMSLP Public Domain oder PDMX Dataset)
- Empfohlene Komponisten Neoclassical: Satie, Debussy, Ravel, Poulenc, Fauré, Einaudi
- Format: .mxl / .xml / .musicxml

SCHRITT 2: MusicXML → ABC konvertieren (LOKAL, kein GPU!)
- Pfade in data/1_batch_xml2abc.py setzen:
  ORI_FOLDER = "../data/my_training_data/musicxml_raw"
  DES_FOLDER = "../data/my_training_data/abc_standard"
- cd data/ && python 1_batch_xml2abc.py

SCHRITT 3: Metadata Headers hinzufügen (KRITISCH!)
Jede ABC Datei braucht am Anfang:
  %Period: Modern
  %Composer: Satie, Erik
  %Instrumentation: Piano
  %end
→ Wir schreiben ein Script das das automatisch macht!
→ %end Separator ist PFLICHT (laut Issue #18 Korrektur von ElectricAlexis)

SCHRITT 4: ABC Preprocessing/Augmentation (LOKAL, kein GPU!)
- Pfade in data/2_data_preprocess.py setzen:
  ORI_FOLDER = "../data/my_training_data/abc_standard"
  INTERLEAVED_FOLDER = "../data/my_training_data/abc_interleaved"
  AUGMENTED_FOLDER = "../data/my_training_data/abc_augmented"
  EVAL_SPLIT = 0.1
- python 2_data_preprocess.py
- Output: abc_augmented_train.jsonl + abc_augmented_eval.jsonl
- Was passiert hier: Transposition in alle Keys (Daten-Augmentierung!), Rest-Reduktion

SCHRITT 5: Fine-tuning auf RunPod A100
- finetune/config.py anpassen:
  DATA_TRAIN_INDEX_PATH = "../data/my_training_data/abc_augmented_train.jsonl"
  DATA_EVAL_INDEX_PATH  = "../data/my_training_data/abc_augmented_eval.jsonl"
  PRETRAINED_PATH = "../gradio/weights_notagenx_p_size_16_p_length_1024_p_layers_20_h_size_1280.pth"
  EXP_TAG = "neoclassical_js"
- cd finetune/ && CUDA_VISIBLE_DEVICES=0 python train-gen.py
- Laut henry-physics: 3 Epochs optimal!

SCHRITT 6: prompts.txt updaten
- Neue Einträge für neue Komponisten hinzufügen
- Format: "Modern_Satie, Erik_Piano"
- Damit erscheinen sie in der Gradio-UI Dropdown

SCHRITT 7 (Optional): CLaMP-DPO für Qualitäts-Boost
- Score: 0.324 → 0.579 → 0.778 nach 2 Iterationen!
- Braucht: CLaMP 2 Weights + M3 Weights
- 1000 generierte Samples als Basis
- Mehrere Iterationen: Inference → Feature Extract → Preference Data → DPO Training
```

### Was aus Issue #18 gelernt wurde
- Source: https://github.com/ElectricAlexis/NotaGen/issues/18
- ManHinnn0509 hat erfolgreich ~100 Alkan-Stücke fine-getuned
- henry-physics hat Schubert Lieder fine-getuned (3 Epochs optimal)
- Colab Notebook (automatisiert): https://colab.research.google.com/drive/1cGllVXgzEa8Vc0CF7ndsm0k7gE-RxvMa
- Alkan fine-tune auf HuggingFace: https://huggingface.co/ManHinnn0509/NotaGenX-with-Alkan/
- **Kritisch:** `%end` Separator in Metadata-Headers nicht vergessen!
- **Kritisch:** Immer NotaGen-X als Basis, nie die base pretrained models!

### Daten-Status
- `data/einaudi/mxl/` - 18 Einaudi MXL Collection Files (vorhanden)
- `data/einaudi/xml/` - 18 MusicXML Versionen (vorhanden)
- `data/einaudi/abc_orig/` - erst 1 ABC File konvertiert (alt, aus Claude Desktop Zeit)
- Weitere Komponisten noch zu beschaffen

## Nächste Schritte
- [ ] Research Bot (Linux, Qwen3 14B) sucht MusicXML Files
- [ ] Bot liefert: docs/neoclassical_musicxml_sources.json
- [ ] Claude Code liest JSON → Download-Script → data/my_training_data/musicxml_raw/
- [ ] Metadata-Header Script schreiben (automatisch %Period/%Composer/%Instrumentation/%end)
- [ ] 1_batch_xml2abc.py durchlaufen
- [ ] 2_data_preprocess.py durchlaufen → train.jsonl + eval.jsonl
- [ ] RunPod Fine-tuning starten

## Datenbeschaffungs-Strategie (entschieden)
- Research Bot übernimmt die Suche komplett
- Brief liegt in: docs/research-bot-brief.md
- Komponisten: Satie, Debussy, Ravel, Fauré, Poulenc + Einaudi, Tiersen, Richter, Frahm, Arnalds
- Einaudi 18x MXL schon lokal vorhanden → mitverwenden
- Format: MusicXML bevorzugt, ABC auch ok
- Ziel: 80-100 Stücke (nach Augmentierung 24x = ~2000+ Samples)

## Forks gescreent
- 120 Forks total, hauptsächlich Clones
- `cumav/NotaGen` - Copilot Multi-Instrument Draft (nicht production-ready)
- `henry-physics/NotaGen_hen` - Aktiv, trainiert mit KPop/Ragtime/VG-Music
- `Irislucent/NotaGen-Continuation` - "update MVP" Oktober 2025
