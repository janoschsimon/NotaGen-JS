# NotaGen Fine-Tuning - Windows Guide (mit Claude Code!)

**Ziel:** NotaGen auf eigenen Stil fine-tunen (z.B. Neoclassical/Orchestral)
**Hardware:** Windows PC mit 4090 (24GB VRAM) ✅
**Tool:** Claude Code hilft bei jedem Schritt!

---

## 🧰 SCHRITT 1: Vorbereitung (einmalig!)

### 1.1 Conda installieren
- Download: https://docs.anaconda.com/miniconda/
- Installer ausführen → "Add to PATH" ✅

### 1.2 CUDA installieren
- CUDA 11.8: https://developer.nvidia.com/cuda-11-8-0-download-archive
- Nach Install: `nvcc --version` → sollte 11.8 zeigen

### 1.3 NotaGen Repository klonen
```bash
git clone https://github.com/ElectricAlexis/NotaGen.git
cd NotaGen
```

### 1.4 Environment erstellen
```bash
conda create --name notagen python=3.10
conda activate notagen
conda install pytorch==2.3.0 pytorch-cuda=11.8 -c pytorch -c nvidia
pip install accelerate optimum -r requirements.txt
```

### 1.5 Weights downloaden - NOTAGEN-X nehmen! (nicht die alten!)
- **NotaGen-X** = DeepSeek-R1 inspiriert, RL-optimiert, beste Version! ✅
- NotaGen-X Weights vom Repo downloaden (README → "NotaGen-X" Section)
- Referenz Fine-tune (Alkan Stil): https://huggingface.co/ManHinnn0509/NotaGenX-with-Alkan/

## ⚠️ GPU REALITÄT (WICHTIG!)

| Task | VRAM | Hardware |
|------|------|----------|
| Inference (Musik generieren) | 24GB | 4090 ✅ |
| Fine-tuning NotaGen-X | 40GB+ | RunPod A100! |
| Fine-tuning NotaGen-Large | >40GB | H800 (Autoren) |

**→ 4090 = nur für Inference!**
**→ Fine-tuning = RunPod A100 (~20€ Budget reicht!)**

Colab Notebook (automatisiert): https://colab.research.google.com/drive/1cGllVXgzEa8Vc0CF7ndsm0k7gE-RxvMa

---

## 📁 SCHRITT 2: Training-Daten besorgen

### Option A: IMSLP (Public Domain, kostenlos!)
- https://imslp.org
- Stil-Empfehlung für Neoclassical:
  - Erik Satie (Gymnopédies, Gnossiennes)
  - Claude Debussy (frühe Werke)
  - Maurice Ravel (Pavane, Sonatine)
  - Francis Poulenc
- Download: MusicXML Format auswählen!
- **~100 Stücke reichen!** (verifiziert in Issue #18 mit Alkan!)
- Metadata Format pro File:
  ```
  %Period: Romantic
  %Composer: Satie, Erik
  %Instrumentation: Piano
  %end
  ```

### Option B: PDMX Dataset (250k Stücke, CC-BY!)
- https://pnlong.github.io/PDMX.demo/
- Größer = besser aber mehr Filterarbeit nötig

### Ordner anlegen:
```
NotaGen/
└── my_training_data/
    ├── musicxml_raw/      ← MusicXML Files hier rein
    ├── abc_standard/      ← wird auto-generiert
    ├── abc_interleaved/   ← wird auto-generiert
    └── abc_augmented/     ← wird auto-generiert
```

---

## 🔄 SCHRITT 3: Daten konvertieren

### 3.1 MusicXML → ABC
```bash
# In data/1_batch_xml2abc.py anpassen:
# ORI_FOLDER = "../my_training_data/musicxml_raw"
# DES_FOLDER = "../my_training_data/abc_standard"

cd data/
python 1_batch_xml2abc.py
```

### 3.2 ABC preprocessing (Augmentation + Index)
```bash
# In data/2_data_preprocess.py anpassen:
# ORI_FOLDER = "../my_training_data/abc_standard"
# INTERLEAVED_FOLDER = "../my_training_data/abc_interleaved"
# AUGMENTED_FOLDER = "../my_training_data/abc_augmented"
# EVAL_SPLIT = 0.1

python 2_data_preprocess.py
```

**Output:** `my_style_train.jsonl` + `my_style_eval.jsonl`

---

## 🎯 SCHRITT 4: Fine-tuning

### 4.1 Config anpassen
In `finetune/config.py`:
```python
DATA_TRAIN_INDEX_PATH = "../my_training_data/abc_augmented/my_style_train.jsonl"
DATA_EVAL_INDEX_PATH  = "../my_training_data/abc_augmented/my_style_eval.jsonl"
PRETRAINED_PATH = "../pretrain/weights_notagen_pretrain_p_size_16_p_length_1024_p_layers_20_c_layers_6_h_size_1280_lr_0.0001_batch_4.pth"
EXP_TAG = "my_neoclassical_style"
```

### 4.2 Training starten
```bash
conda activate notagen
cd finetune/
python train-gen.py
```

⏱️ Erwartete Zeit auf 4090: 2-6 Stunden (je nach Datenmenge)

---

## 🎵 SCHRITT 5: Inference (Musik generieren!)

### 5.1 Config anpassen
In `inference/config.py`:
```python
INFERENCE_WEIGHTS_PATH = '../finetune/weights_notagen_my_neoclassical_style_...'
NUM_SAMPLES = 10
```

### 5.2 Generieren
```bash
cd inference/
python inference.py
```

**Output:** ABC Notation Files in `output/`

### 5.3 ABC → MusicXML konvertieren
```bash
# In data/ - abc2xml.py nutzen
python abc2xml.py input.abc output.xml
```

Dann → Digital Director → Cubase! 🎬

---

## 🚀 OPTIONAL: CLaMP-DPO (Stil weiter verbessern)

Wenn Fine-tuning gut läuft aber Stil noch nicht perfekt:
→ CLaMP-DPO macht 2-3 Iterationen und verbessert Style-Score massiv
→ Score: 0.324 → 0.778 (!) nach 2 Iterationen
→ Separates Kapitel - erst wenn Basis-Fine-tuning klappt!

---

## 🆘 TROUBLESHOOTING mit Claude Code

Bei Fehlern: Einfach die Fehlermeldung in Claude Code einfügen!

**Häufige Probleme:**
- `CUDA out of memory` → Batch Size reduzieren in config.py
- `Module not found` → `pip install <modul>` im notagen environment
- `xml2abc conversion failed` → MusicXML Format prüfen (manche IMSLP Files sind PDFs!)

---

## 📊 ERWARTETE ERGEBNISSE

| Training Data | Fine-tune Zeit (4090) | Stil-Qualität |
|--------------|----------------------|---------------|
| 50 Stücke | ~1-2h | Basis |
| 100 Stücke | ~2-4h | Gut |
| 200+ Stücke | ~4-8h | Sehr gut |

---

## 🔗 LINKS

- NotaGen Repo: https://github.com/ElectricAlexis/NotaGen
- IMSLP: https://imslp.org
- PDMX Dataset: https://pnlong.github.io/PDMX.demo/
- CUDA 11.8: https://developer.nvidia.com/cuda-11-8-0-download-archive

---

## 🤖 CLAUDE CODE WORKFLOW (Windows!)

**Schritt 1: CC durch Repo wühlen lassen**
```
"Lies das NotaGen Repo und erkläre mir die Fine-tuning Pipeline"
```

**Schritt 2: IMSLP Daten vorbereiten**
```
"Konvertiere alle MusicXML in /my_data/ zu ABC und füge Metadata hinzu"
```
CC schreibt/führt die Skripte aus!

**Schritt 3: RunPod starten**
- A100 40GB mieten
- Repo + Daten hochladen
- CC managed das Training

**Schritt 4: Fine-tuned Model zurück auf 4090**
- Inference lokal (24GB reicht!)
- ABC Output → MusicXML konvertieren

**Schritt 5: Digital Director Pipeline**
```
NotaGen-X Output (ABC)
    ↓
abc2xml.py → MusicXML
    ↓
Digital Director (~/Digital_Director/) → humanisiert
    ↓
Cubase → fertiger Film-Score! 🎬🎵
```

⚠️ Digital Director Repo: https://github.com/janoschsimon/Digital_Director
→ CC kann das direkt integrieren und verwalten!

---

**Erstellt:** 2026-02-15
**Status:** Guide v1.0 - Ready für Windows CC Session!
