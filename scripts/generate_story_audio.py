#!/usr/bin/env python3
"""Generate narration for explicitly opted-in Hugo stories.

Front matter must include audio_generate: true. Audio is published in
static/audio/stories/<story-slug>.mp3; add audio: /audio/stories/<slug>.mp3
to the story front matter to expose its player.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
STORIES = ROOT / "content" / "stories"
OUTPUT = ROOT / "static" / "audio" / "stories"

def frontmatter(text):
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("---\n", 2)
    if len(parts) != 3:
        return {}, text
    meta = {}
    for line in parts[1].splitlines():
        match = re.match(r"^([\w-]+):\s*(.*)$", line)
        if match:
            meta[match.group(1)] = match.group(2).strip().strip('"\'')
    return meta, parts[2]

def narration(text):
    text = re.sub(r"(?ms)^<figure\b.*?</figure>\s*", "", text)
    text = re.sub(r"(?ms)^!\[[^]]*\]\([^)]*\)\s*$", "", text)
    text = re.sub(r"(?m)^\s*\*?(?:Photo|Image|Caption):.*$", "", text, flags=re.I)
    text = re.sub(r"(?ms)^```.*?^```\s*", "", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"!\[[^]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"(?m)^#{1,6}\s*", "", text)
    text = re.sub(r"[*_`]", "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    key = os.getenv("ELEVENLABS_API_KEY")
    voice = os.getenv("ELEVENLABS_VOICE_ID")
    model = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
    if not args.dry_run and (not key or not voice):
        sys.exit("Set ELEVENLABS_API_KEY secret and ELEVENLABS_VOICE_ID variable.")
    files = sorted(STORIES.rglob("*.md")) if STORIES.exists() else []
    for file in files:
        meta, body = frontmatter(file.read_text(encoding="utf-8"))
        if meta.get("audio_generate", "").lower() != "true":
            continue
        slug = file.stem if file.stem != "index" else file.parent.name
        slug = re.sub(r"[^a-zA-Z0-9_-]", "-", slug)
        target = OUTPUT / (slug + ".mp3")
        content = narration(body)
        if not content:
            continue
        if target.exists():
            print(f"Skipping existing audio: {target.relative_to(ROOT)}")
            continue
        print(f"Generating: {file.relative_to(ROOT)} -> {target.relative_to(ROOT)}")
        if args.dry_run:
            continue
        request = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128",
            data=json.dumps({"text": content, "model_id": model}).encode(),
            headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                audio = response.read()
        except Exception as exc:
            sys.exit(f"ElevenLabs generation failed for {file}: {exc}")
        OUTPUT.mkdir(parents=True, exist_ok=True)
        target.write_bytes(audio)
        print(f"Saved {len(audio)} bytes")
if __name__ == "__main__":
    main()
