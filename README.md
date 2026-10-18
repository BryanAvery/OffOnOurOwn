# Off On Our Own - GitHub/Hugo migration starter

This starter contains the WordPress content imported into Hugo files with the original permalink URL preserved.
It is a **preview only** and is deliberately missing the photo/video files and some WordPress-specific widgets.
Read `migration/MIGRATION-AUDIT.md` first.

## Running locally

1. Install [Hugo](https://gohugo.io/installation/) (extended edition is fine).
2. In this directory, run `hugo server --disableFastRender` and visit the address printed by Hugo.
3. Review original stories and destination entries. Check `migration/review-queue.csv`.

## GitHub Pages preview (do not switch the domain yet)

1. Create a new repository, for example `BryanAvery/offonourown`.
2. Upload **the files in this directory**, not the raw original WordPress XML.
3. In GitHub repository Settings > Pages select **GitHub Actions** as the source.
4. Push to `main`; the included action will build and publish a preview.
5. Check image placeholders, old galleries, TravelPod and Flickr external assets, map embeds and legacy shortcodes.

**The preview does not include a CNAME file.** Only set your custom domain once the content and media are complete.

## Media migration

The XML does not contain media binaries. Export/download the full `wp-content/uploads` folder from your existing WordPress hosting.
After assessing the total size and GitHub Pages' size limits, either:
- copy the image files to `static/wp-content/uploads/<year>/<month>/<filename>` to retain URLs when the custom domain moves, or
- use an external media host and rewrite references in the imported content.

For media stored outside WordPress (TravelPod, Flickr), test URLs individually and replace unavailable references with original images where possible.

## Safety

Do not commit WordPress database backups, raw WXR exports, private drafts, contact-form submissions, access keys, or passwords. This starter includes published content only. Inspect the content files before publishing publicly.

## Audit the Google Drive `uploads.zip` locally

The media archive `uploads.zip` is 1,928,355,434 bytes (about 1.93 GB), which is
larger than this workspace's single-file Google Drive transfer limit. There is no
need to re-upload it or extract it to run the following audit.

On your Mac, download `uploads.zip` from Google Drive and place it beside this
project's `README.md`. Open Terminal in the project folder, then run:

```bash
python3 scripts/audit_media.py ./uploads.zip
```

The audit reads the ZIP file index without decompressing the photographs. It
compares WordPress attachment filenames and references inside all converted
content against the files in the ZIP. Look in the `media-audit/` folder for:

- `media-summary.json` - counts and estimated uncompressed size.
- `media-audit.csv` - one row per expected path.
- `missing-media.csv` - files not found or with case differences.

If you already have `wp-content/uploads` extracted, pass that folder instead.
The audit makes no changes to your archive or live WordPress site. The legacy
Flickr and TravelPod resources are external and not covered by this local audit.

Keep `uploads.zip` **out of Git**. Don't point the live domain at the prototype
until media hosting and legacy links have been tested.
