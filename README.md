# VocabQuest Over-The-Air (OTA) Content Packs

Welcome to the official content repository for **VocabQuest** (`DarkWolfHunter007/VocabQuest-Content-Packs`).

This repository provides live, Over-The-Air (OTA) content delivery for VocabQuest players worldwide. New vocabulary expansion packs, themed crosswords, and word search puzzles can be created, reviewed, and published here without requiring client app store updates.

---

## 📁 Repository Structure

```tree
VocabQuest-Content-Packs/
├── README.md                      # Content authoring and contribution guide
├── manifests.json                 # Root alias/fallback content catalog
└── content/
    ├── manifests.json             # Primary content catalog listing all available packs
    └── packs/
        ├── science_pack_v1.json   # Science & Technology expansion pack (v1)
        ├── nature_pack_v1.json    # Wild Wonders & Nature expansion pack (v1)
        └── space_pack_v1.json     # Space & Astronomy expansion pack (v1)
```

---

## 🚀 How OTA Content Ingestion Works

1. **Manifest Discovery**: When connected to the internet, VocabQuest queries:
   `https://raw.githubusercontent.com/DarkWolfHunter007/VocabQuest-Content-Packs/main/content/manifests.json`
   *(with graceful fallback to root `manifests.json`)*.
2. **Catalog Differential**: The local `ContentSyncService` checks cached pack versions against remote manifest versions.
3. **Streamed Download**: New or updated packs are fetched from `content/packs/{pack_id}.json`.
4. **Strict Client-Side Validation**: The `ContentValidator` validates words, grid dimensions, letter intersections, and profanity safety before persisting.
5. **Instant Ingestion**: Validated words and puzzles are instantly registered in `DictionaryRepository` and `PuzzleRepository` without requiring app restart.

---

## 🛠️ Content Pack Schema Specification

Every pack file in `content/packs/` must be a valid JSON object matching the `ContentPack` schema:

```json
{
  "id": "pack_space_v1",
  "version": 1,
  "name": "Space & Astronomy Pack",
  "description": "Deep space phenomena, planetary orbits, and interstellar vocabulary.",
  "category": "Space",
  "difficulty": "Medium",
  "isBuiltIn": false,
  "minAppVersion": "1.0.0",
  "words": [ ... ],
  "crosswordPuzzles": [ ... ],
  "wordSearchPuzzles": [ ... ]
}
```

### 1. Word Entry Template

```json
{
  "id": "galaxy",
  "word": "GALAXY",
  "partOfSpeech": "n.",
  "phonetic": "/ˈɡæl.ək.si/",
  "definition": "A system of millions or billions of stars, together with gas and dust.",
  "exampleSentence": "The Milky Way is a spiral galaxy containing billions of solar systems.",
  "difficulty": "medium",
  "category": "Space",
  "tags": ["astronomy", "cosmos"]
}
```

**Word Validation Constraints:**
- `word`: 2 to 20 characters, alphabetic letters only (`A-Z`), uppercase.
- `partOfSpeech`: Common English abbreviation (e.g., `n.`, `v.`, `adj.`, `adv.`).
- `phonetic`: IPA pronunciation format (e.g., `/ˈplæn.ɪt/`).
- `definition`: Minimum length of 5 characters.
- `difficulty`: One of `beginner`, `easy`, `medium`, `hard`, `expert`.
- **Profanity Filter**: Words containing inappropriate or offensive terms are rejected automatically.

---

### 2. Crossword Puzzle Template

```json
{
  "levelId": "space_cw_1",
  "levelNumber": 1,
  "title": "Cosmic Voyages",
  "difficulty": "medium",
  "gridWidth": 8,
  "gridHeight": 8,
  "targetWords": [
    "GALAXY",
    "SATURN",
    "NEBULA",
    "ORBIT",
    "COMET"
  ],
  "clues": [
    {
      "number": 1,
      "direction": "across",
      "clue": "A massive cosmic system of billions of stars and planetary systems.",
      "answer": "GALAXY",
      "startRow": 1,
      "startCol": 1
    },
    {
      "number": 2,
      "direction": "down",
      "clue": "The sixth planet famous for its majestic planetary rings.",
      "answer": "SATURN",
      "startRow": 0,
      "startCol": 2
    },
    {
      "number": 3,
      "direction": "across",
      "clue": "An interstellar cloud of luminescent gas and stellar dust.",
      "answer": "NEBULA",
      "startRow": 5,
      "startCol": 2
    },
    {
      "number": 4,
      "direction": "down",
      "clue": "The gravitational path traced by an orbiting celestial body.",
      "answer": "ORBIT",
      "startRow": 3,
      "startCol": 4
    },
    {
      "number": 5,
      "direction": "across",
      "clue": "An icy celestial body that develops a glowing tail near a star.",
      "answer": "COMET",
      "startRow": 7,
      "startCol": 0
    }
  ],
  "targetSecondsGoal": 75
}
```

**Crossword Validation Constraints:**
- `gridWidth` and `gridHeight` must be $\ge 3$.
- `startRow` and `startCol` are 0-indexed.
- `startCol + answer.length` must be $\le gridWidth$ for `across` clues.
- `startRow + answer.length` must be $\le gridHeight$ for `down` clues.
- All intersecting cells **must share identical characters**.
- Every clue answer **must exist** in the pack's `words` glossary.

---

### 3. Word Search Puzzle Template

```json
{
  "levelId": "space_ws_1",
  "levelNumber": 1,
  "title": "Interstellar Odyssey",
  "difficulty": "medium",
  "gridSize": 10,
  "wordsToFind": [
    "GALAXY",
    "SATURN",
    "NEBULA",
    "ORBIT",
    "COMET",
    "QUASAR"
  ],
  "targetSecondsGoal": 90,
  "requiredCrosswordStars": 0
}
```

**Word Search Validation Constraints:**
- `gridSize`: Between 4 and 25.
- Length of each word in `wordsToFind` must be $\le gridSize$.
- Every word in `wordsToFind` **must exist** in the pack's `words` glossary.

---

## 📋 Catalog Manifest Registration

When adding or updating a pack, always register it in both `content/manifests.json` and root `manifests.json`:

```json
[
  {
    "id": "pack_space_v1",
    "version": 1,
    "name": "Space & Astronomy Pack",
    "description": "Deep space phenomena, planetary orbits, and interstellar vocabulary.",
    "category": "Space",
    "difficulty": "Medium",
    "wordCount": 6,
    "puzzleCount": 2,
    "minAppVersion": "1.0.0",
    "sizeBytes": 4600
  }
]
```

---

## 🔄 Publishing Workflow

1. Create a branch for your new pack:
   ```bash
   git checkout -b feature/pack-history-v1
   ```
2. Add your pack JSON file to `content/packs/history_pack_v1.json`.
3. Add the entry to `content/manifests.json` and `manifests.json`.
4. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "feat(content): add History & Ancient Civilizations expansion pack v1"
   git push origin feature/pack-history-v1
   ```
5. Merge into `main`. VocabQuest app instances will discover and download the new pack automatically upon their next online sync!
