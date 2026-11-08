#!/usr/bin/env python3
"""Validate VocabQuest content packs before they go live.

Everything on `main` is served Over-The-Air to every player, so this script
mirrors the app's ContentValidator rules (lib/content/validation/content_validator.dart)
and fails CI if any manifest or pack would be rejected or is unsafe.

Usage: python3 scripts/validate_packs.py [repo_root]
"""
import json
import re
import sys
from pathlib import Path

PACK_ID = re.compile(r"^[a-z0-9_]{1,64}$")
ALPHA = re.compile(r"^[A-Za-z]+$")
MAX_BYTES = 2 * 1024 * 1024
MAX_WORDS = 2000
MAX_PUZZLES = 500
MAX_CLUES = 200
MAX_GRID = 30
SHORT = 120
LONG = 1000


def check_pack(path: Path, errors: list[str]) -> str | None:
    def err(msg: str) -> None:
        errors.append(f"{path}: {msg}")

    if path.stat().st_size > MAX_BYTES:
        err(f"file is larger than {MAX_BYTES} bytes")
        return None
    try:
        pack = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        err(f"invalid JSON: {e}")
        return None
    if not isinstance(pack, dict):
        err("pack must be a JSON object")
        return None

    pack_id = pack.get("id", "")
    if not isinstance(pack_id, str) or not PACK_ID.match(pack_id):
        err(f"id {pack_id!r} must match {PACK_ID.pattern}")
    elif path.stem != pack_id:
        err(f"file name must be {pack_id}.json")
    if not isinstance(pack.get("version"), int) or pack["version"] < 1:
        err("version must be an integer >= 1")
    for field, limit in (("name", SHORT), ("description", LONG), ("category", SHORT), ("difficulty", SHORT)):
        value = pack.get(field, "")
        if not isinstance(value, str) or len(value) > limit:
            err(f"{field} must be a string of at most {limit} characters")
    if not str(pack.get("name", "")).strip():
        err("name cannot be empty")

    words = pack.get("words") or []
    crosswords = pack.get("crosswordPuzzles") or []
    searches = pack.get("wordSearchPuzzles") or []
    if len(words) > MAX_WORDS:
        err("too many words")
        return pack_id
    if len(crosswords) + len(searches) > MAX_PUZZLES:
        err("too many puzzles")
        return pack_id

    glossary: set[str] = set()
    for w in words:
        text = str(w.get("word", "")).strip().upper()
        if not ALPHA.match(text) or not 2 <= len(text) <= 20:
            err(f"word {text!r} must be 2-20 letters A-Z")
        if text in glossary:
            err(f"duplicate word {text!r}")
        glossary.add(text)
        definition = str(w.get("definition", "")).strip()
        if len(definition) < 5 or len(definition) > LONG:
            err(f"word {text!r} definition must be 5-{LONG} characters")
        if len(str(w.get("exampleSentence", ""))) > LONG:
            err(f"word {text!r} example sentence too long")
        if not str(w.get("partOfSpeech", "")).strip():
            err(f"word {text!r} missing partOfSpeech")
        for field in ("id", "partOfSpeech", "phonetic", "category", "difficulty"):
            if len(str(w.get(field, ""))) > SHORT:
                err(f"word {text!r} field {field} too long")

    for cw in crosswords:
        title = cw.get("title", "?")
        width, height = cw.get("gridWidth"), cw.get("gridHeight")
        if not isinstance(width, int) or not isinstance(height, int) or not (3 <= width <= MAX_GRID and 3 <= height <= MAX_GRID):
            err(f"crossword {title!r} grid must be 3-{MAX_GRID} wide and high")
            continue
        clues = cw.get("clues") or []
        if len(clues) > MAX_CLUES:
            err(f"crossword {title!r} has too many clues")
            continue
        grid: dict[tuple[int, int], str] = {}
        for clue in clues:
            answer = str(clue.get("answer", "")).upper()
            row, col = clue.get("startRow", -1), clue.get("startCol", -1)
            direction = clue.get("direction")
            if not ALPHA.match(answer):
                err(f"crossword {title!r} answer {answer!r} invalid")
                continue
            if answer not in glossary:
                err(f"crossword {title!r} answer {answer!r} not in pack words")
            if len(str(clue.get("clue", ""))) > LONG:
                err(f"crossword {title!r} clue text too long")
            if not isinstance(row, int) or not isinstance(col, int) or not (0 <= row < height and 0 <= col < width):
                err(f"crossword {title!r} clue {answer!r} starts outside the grid")
                continue
            if direction == "across":
                cells = [(row, col + i) for i in range(len(answer))]
            elif direction == "down":
                cells = [(row + i, col) for i in range(len(answer))]
            else:
                err(f"crossword {title!r} clue {answer!r} has invalid direction {direction!r}")
                continue
            if any(r >= height or c >= width for r, c in cells):
                err(f"crossword {title!r} clue {answer!r} runs off the grid")
                continue
            for cell, letter in zip(cells, answer):
                if grid.setdefault(cell, letter) != letter:
                    err(f"crossword {title!r} letter clash at {cell}")

    for ws in searches:
        title = ws.get("title", "?")
        size = ws.get("gridSize")
        targets = ws.get("wordsToFind") or []
        if not isinstance(size, int) or not 4 <= size <= 25:
            err(f"word search {title!r} gridSize must be 4-25")
            continue
        if not targets or len(targets) > MAX_CLUES:
            err(f"word search {title!r} needs 1-{MAX_CLUES} words")
        for t in targets:
            t = str(t).upper()
            if len(t) > size:
                err(f"word search {title!r} word {t!r} longer than grid")
            if t not in glossary:
                err(f"word search {title!r} word {t!r} not in pack words")
    return pack_id


def check_manifest(path: Path, pack_ids: dict[str, int], errors: list[str]) -> None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        errors.append(f"{path}: invalid JSON: {e}")
        return
    entries = data if isinstance(data, list) else (data.get("manifests") or data.get("packs") or [])
    for entry in entries:
        pid = entry.get("id", "")
        if not isinstance(pid, str) or not PACK_ID.match(pid):
            errors.append(f"{path}: manifest id {pid!r} must match {PACK_ID.pattern}")
        elif pid not in pack_ids:
            errors.append(f"{path}: manifest lists {pid!r} but content/packs/{pid}.json is missing")
        elif entry.get("version") != pack_ids[pid]:
            errors.append(f"{path}: manifest version for {pid!r} does not match the pack file")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    errors: list[str] = []
    pack_ids: dict[str, int] = {}
    for path in sorted((root / "content" / "packs").glob("*.json")):
        pid = check_pack(path, errors)
        if pid:
            pack_ids[pid] = json.loads(path.read_text(encoding="utf-8")).get("version")
    for manifest in (root / "content" / "manifests.json", root / "manifests.json"):
        if manifest.exists():
            check_manifest(manifest, pack_ids, errors)
    for e in errors:
        print(f"ERROR {e}")
    print(f"Checked {len(pack_ids)} packs: {'FAILED' if errors else 'OK'}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
