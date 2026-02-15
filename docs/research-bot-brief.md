# Research Bot Brief: Neoclassical MusicXML Dataset

## Ziel
Finde direkte Download-Links für MusicXML oder ABC Notation Dateien von Neoclassical/Impressionist Komponisten für ein KI-Musikgenerierungs-Trainingsprojekt.

## Gesuchte Komponisten (alle Public Domain!)
- **Erik Satie** (1866-1925)
- **Claude Debussy** (1862-1918)
- **Maurice Ravel** (1875-1937)
- **Gabriel Fauré** (1845-1924)
- **Francis Poulenc** (1899-1963)

## Gesuchte Werke
Piano-Stücke bevorzugt. Kein Orchester, keine Oper.
Ziel: 80-100 Stücke total.

Bekannte Prioritäts-Werke:
- Satie: Gymnopédies (1-3), Gnossiennes (1-6), Nocturnes, 4 Ogives, Avant-dernières pensées
- Debussy: Arabesques (1-2), Clair de Lune, Children's Corner, Préludes Book 1+2, Images, Estampes
- Ravel: Pavane pour une infante défunte, Miroirs, Sonatine, Valses nobles et sentimentales, Jeux d'eau
- Fauré: Nocturnes (1-13), Barcarolles, Impromptus, Ballade op.19
- Poulenc: 3 Novelettes, Nocturnes, Impromptus, Mouvements perpétuels

## Bevorzugte Quellen
1. https://github.com/fosfrancesco/asap-dataset (direkt clonebar, hat Debussy+Ravel MusicXML)
2. IMSLP API: https://imslp.org/api.php (nach MusicXML/MXL Files filtern)
3. https://github.com/musetrainer/library (MXL files)
4. OpenScore GitHub repos
5. MuseScore.com public domain pieces (MusicXML download)
6. PDMX Zenodo Metadaten filtern nach diesen Komponisten

## Datei-Formate (Priorität)
1. `.mxl` (compressed MusicXML) ← beste Wahl
2. `.musicxml` oder `.xml` (uncompressed MusicXML)
3. `.abc` (ABC Notation) ← auch ok, etwas weniger bevorzugt

## Gewünschtes Output-Format (JSON)

```json
[
  {
    "url": "https://direkte-download-url.com/datei.mxl",
    "composer": "Satie, Erik",
    "piece": "Gymnopédie No. 1",
    "format": "mxl",
    "instrumentation": "Piano",
    "period": "Modern",
    "source": "IMSLP",
    "license": "Public Domain"
  },
  {
    "url": "https://...",
    "composer": "Debussy, Claude",
    "piece": "Arabesque No. 1",
    "format": "musicxml",
    "instrumentation": "Piano",
    "period": "Romantic",
    "source": "asap-dataset GitHub",
    "license": "CC-BY 4.0"
  }
]
```

## Wichtige Hinweise
- NUR direkte Download-URLs (nicht Seiten-URLs)
- NUR Public Domain oder CC-BY Lizenzen
- Wenn IMSLP: File-ID oder direkten API-Link verwenden
- Duplikate vermeiden (nicht dasselbe Stück mehrfach)
- Instrumentation: Piano solo bevorzugt, Piano duo / Chamber ok
- NICHT: Orchestral, Vocal, Oper

## Was wir NICHT brauchen
- PDF Dateien
- MIDI Dateien (nur wenn kein MusicXML verfügbar)
- Arrangements/Bearbeitungen (Originalversionen bevorzugt)

## Zusätzliche Komponisten (moderner Stil, privates Research-Projekt)
Gerne auch:
- **Ludovico Einaudi** (lokal schon 18 MXL vorhanden, mehr = besser)
- **Yann Tiersen** (Amélie OST Stil)
- **Max Richter** (Neoclassical)
- **Nils Frahm** (Contemporary Piano)
- **Ólafur Arnalds**
- **Johann Johannsson**

## Hinweis zu ASAP Dataset
Das ASAP Dataset auf GitHub hat direkte MusicXML Dateien:
- Repo: https://github.com/fosfrancesco/asap-dataset
- Metadata CSV mit Pfaden: metadata.csv
- Enthält bestätigt: Debussy (2 Scores), Ravel (4 Scores)
- Einfach alle xml_score Pfade für Debussy + Ravel aus metadata.csv extrahieren

## Erwartetes Ergebnis
JSON Array mit 80-100 Einträgen, bereit zum Download.
Dateiname: `neoclassical_musicxml_sources.json`
