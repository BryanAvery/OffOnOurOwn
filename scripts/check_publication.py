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


# Every migrated [flickr_set] shortcode must display its corresponding Flickr album.
import re

shortcode_re = re.compile(r"""\[flickr_set\s+id=["']?([0-9]+)["']?\s*\]""", re.IGNORECASE)
flickr_pages = 0
flickr_embeds = 0
for source_file in Path("content").rglob("*.html"):
    source = source_file.read_text(encoding="utf-8")
    album_ids = shortcode_re.findall(source)
    if not album_ids:
        assert "[flickr_set" not in source.lower(), f"Unrecognised Flickr shortcode in {source_file}"
        continue

    url = re.search(r"""(?m)^url:\s*['"]?(/[^'"\s]+)""", source)
    assert url, f"Missing published URL for {source_file}"
    output_path = str(Path(url.group(1).lstrip("/")) / "index.html")
    rendered = page(output_path)
    assert "[flickr_set" not in rendered.lower(), f"Unconverted Flickr shortcode on {output_path}"

    for album_id in album_ids:
        assert f'src="https://embedr.flickr.com/photosets/{album_id}"' in rendered, (
            f"Missing embedded Flickr album {album_id} on {output_path}"
        )
        assert f'https://www.flickr.com/photos/offonourown/albums/{album_id}/' in rendered, (
            f"Missing Flickr album link {album_id} on {output_path}"
        )
    flickr_pages += 1
    flickr_embeds += len(album_ids)

print(f"Flickr album checks passed: {flickr_embeds} embeds across {flickr_pages} content pages.")

print("Publication smoke checks passed: domain, stylesheet, articles, media URL rewrites and indexing.")
