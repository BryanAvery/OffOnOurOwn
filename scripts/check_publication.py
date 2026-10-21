#!/usr/bin/env python3
"""Smoke-test key pages from the generated Hugo site before publishing."""
from pathlib import Path
import sys

public = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("public")


def page(path: str) -> str:
    target = public / path
    if not target.is_file():
        raise AssertionError(f"Missing generated page: {target}")
    return target.read_text(encoding="utf-8")


home = page("index.html")
assert '/css/site.css' in home, "Stylesheet must use the custom-domain root"
assert 'href="/OffOnOurOwn/' not in home, "Old GitHub project subdirectory remains"
assert "https://photos.offonourown.co.uk/" in home, "Home hero should use available photo metadata"

laos = page("laos/index.html")
assert "https://photos.offonourown.co.uk/2016/05/shapeimage_4-78-300x225.png" in laos
assert 'src="/wp-content/uploads/' not in laos

hue = page("packages/hue/index.html")
assert "https://photos.offonourown.co.uk/2016/05/shapeimage_4-80-300x225.png" in hue
assert "test.offonourownagain.com" not in hue

prague = page("prague-beckons/index.html")
assert "https://photos.offonourown.co.uk/2024/08/WhatsApp-Image" in prague

robots = page("robots.txt")
assert "Disallow: /" not in robots, "Live site must not be blocked from indexing"
assert (public / "CNAME").read_text(encoding="utf-8").strip() == "offonourown.co.uk"

print("Publication smoke checks passed: domain, stylesheet, articles, media URL rewrites and indexing.")
