# NotaGen-JS - Claude Code Kontext

## Projekt-Ziel
Fine-tuning von NotaGen-X auf Neoclassical/Film-Score Stil.
Output → Digital Director → Cubase → fertiger Film-Score.

## Hardware
- **Lokal (4090, 24GB VRAM):** Inference only
- **RunPod A100 (40GB+):** Fine-tuning (~20€ Budget)

## Pipeline
```
IMSLP MusicXML
    ↓
data/1_batch_xml2abc.py → ABC Standard
    ↓
data/2_data_preprocess.py → ABC Augmented (train.jsonl + eval.jsonl)
    ↓
RunPod: finetune/train-gen.py
    ↓
Lokal: gradio/final-gui.py → Inference
    ↓
abc2xml.py → MusicXML
    ↓
Digital Director (~/Digital_Director/) → humanisiert
    ↓
Cubase → Film-Score
```

## Git Setup
- **origin:** https://github.com/janoschsimon/NotaGen-JS (eigener Fork, privat)
- **upstream:** https://github.com/ElectricAlexis/NotaGen (original)
- Updates holen: `git pull upstream main`
- Sichern: `git push`

## Wichtige Dateien
- `gradio/final-gui.py` - Haupt-GUI mit Batch + Parameter-Sliders
- `gradio/x_notagen-vram-optimized.py` - VRAM-optimierte Version
- `gradio/config.py` - Inference Parameter (TOP_K=9, TOP_P=0.9, TEMP=1.2)
- `gradio/weights_notagenx_p_size_16_p_length_1024_p_layers_20_h_size_1280.pth` - NotaGen-X Weights (lokal, nicht auf GitHub!)
- `data/1_batch_xml2abc.py` - MusicXML → ABC Konvertierung
- `NOTAGEN_WINDOWS_GUIDE.md` - Vollständiger Setup-Guide

## Trainingsdaten-Ziel
**Stil:** Neoclassical (Satie, Debussy, Ravel, Poulenc, Einaudi)
**Menge:** ~100 Stücke (reicht laut Issue #18)
**Format:** MusicXML von IMSLP → ABC → augmented JSONL
**Ordnerstruktur:**
```
data/my_training_data/
    musicxml_raw/    ← IMSLP Downloads hier
    abc_standard/    ← auto-generiert
    abc_interleaved/ ← auto-generiert
    abc_augmented/   ← train.jsonl + eval.jsonl
```

## Metadata Format (pro ABC File)
```
%Period: Modern
%Composer: Satie, Erik
%Instrumentation: Piano
%end
```

## Status (2026-02-15)
- [x] NotaGen-X läuft lokal auf 4090
- [x] Inference GUI (final-gui.py) funktioniert
- [x] Upstream gemergt (torch.autocast + inference_mode)
- [x] GitHub eingerichtet (janoschsimon/NotaGen-JS)
- [x] CLAUDE.md + docs/sessions/ Struktur angelegt
- [x] Research Bot Brief geschrieben (docs/research-bot-brief.md)
- [ ] Research Bot liefert neoclassical_musicxml_sources.json
- [ ] Download-Script ausführen → data/my_training_data/musicxml_raw/
- [ ] data/1_batch_xml2abc.py durchlaufen
- [ ] Metadata-Header Script schreiben + ausführen
- [ ] data/2_data_preprocess.py durchlaufen → train.jsonl + eval.jsonl
- [ ] RunPod A100 Fine-tuning
- [ ] prompts.txt mit neuen Komponisten updaten
- [ ] (Optional) CLaMP-DPO Iterationen
- [ ] Digital Director Integration testen

## Notizen
- Einaudi 18x MXL in data/einaudi/mxl/ - VERWENDEN!
- Research Bot (Linux, Qwen3 14B, 30 Engines) übernimmt Datenbeschaffung
- Bot Output erwartet: docs/neoclassical_musicxml_sources.json
- Nach JSON-Lieferung: ich schreibe Download-Script + Metadata-Header Script
- `#training/` und persönliche Ordner sind in .gitignore
- Digital Director Repo: https://github.com/janoschsimon/Digital_Director (privat)
- Modell-Klarheit: NUR NotaGen-X verwenden, nie base pretrained models!
- 3 Epochs optimal laut henry-physics (Issue #18)
- Nach Augmentierung (24 Keys): ~30 Stücke → ~720 Trainingssamples

## Wichtige Erkenntnisse (Issue #18)
- %end Separator in Metadata-Headers PFLICHT
- Format: %Period\n%Composer\n%Instrumentation\n%end
- prompts.txt Format: "Modern_Satie, Erik_Piano"
- Colab Notebook: https://colab.research.google.com/drive/1cGllVXgzEa8Vc0CF7ndsm0k7gE-RxvMa
