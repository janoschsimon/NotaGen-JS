# Research Bot Brief: Neoclassical MusicXML Dataset

## Ziel
Finde direkte Download-Links für MusicXML oder ABC Notation Dateien von Neoclassical/Impressionist Komponisten für ein KI-Musikgenerierungs-Trainingsprojekt.

## WICHTIG: Nur diese 2 Komponisten! (Stil-Fokus!)
- **Erik Satie** (1866-1925) ← PRIORITÄT 1
- **Ludovico Einaudi** ← PRIORITÄT 2

Warum nur 2? Zu viele Stile = schlechtes Training (wie Flux mit 10.000 Gesichtern).
Satie + Einaudi teilen dieselbe DNA: minimalistisch, pulsierend, intim, piano-fokussiert.
Das ist der Ziel-Sound für einen KI-Kurzfilm Score.

## Gesuchte Werke
NUR Piano solo. Kein Orchester, keine Oper, kein Chor.
Ziel: 80-100 Stücke total.

**Satie Prioritäts-Werke:**
- Gymnopédies (1-3)
- Gnossiennes (1-6)
- Nocturnes (1-5)
- 4 Ogives
- Avant-dernières pensées
- Descriptions automatiques
- Enfantillages pittoresques
- Pièces froides
- Je te veux
- Danses gothiques
- Chapitres tournés en tous sens

**Einaudi Prioritäts-Werke:**
- Experience, Nuvole Bianche, Una Mattina, Le Onde, Divenire
- I Giorni, Eros, Fly, Primavera, Oltremare
- Alles aus: Le Onde, I Giorni, Divenire, In a Time Lapse, Islands
- Die 18x MXL files aus "The Einaudi Collection" sind schon lokal vorhanden!

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

## Nicht gewünscht
- Andere Komponisten - Fokus ist Satie + Einaudi!
- Orchestral, Vocal, Oper, Chor
- PDF oder MIDI Dateien

## Hinweis zu ASAP Dataset
Das ASAP Dataset auf GitHub hat direkte MusicXML Dateien:
- Repo: https://github.com/fosfrancesco/asap-dataset
- Metadata CSV mit Pfaden: metadata.csv
- Enthält bestätigt: Debussy (2 Scores), Ravel (4 Scores)
- Einfach alle xml_score Pfade für Debussy + Ravel aus metadata.csv extrahieren

## Erwartetes Ergebnis
JSON Array mit 80-100 Einträgen, bereit zum Download.
Dateiname: `neoclassical_musicxml_sources.json`
