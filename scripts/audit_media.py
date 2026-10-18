#!/usr/bin/env python3
"""Audit a WordPress uploads directory or ZIP against a Hugo migration.
Uses only the Python 3 standard library. A ZIP is read via its directory index;
photo bytes are not extracted or uploaded anywhere.
"""
import argparse
import csv
import html
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / 'migration' / 'media-manifest.csv'
CONTENT = ROOT / 'content'
REF = re.compile(r'/wp-content/uploads/([^\s"\'<>?#)]+)', re.IGNORECASE)

def normalize(name):
    name = unquote(html.unescape(str(name))).replace('\\', '/').lstrip('/')
    # ZIPs can have a top-level uploads/ or wp-content/uploads/ folder
    lower = name.lower()
    for marker in ('/wp-content/uploads/', '/uploads/'):
        if marker in lower:
            index = lower.rindex(marker)
            return name[index + len(marker):]
    for prefix in ('wp-content/uploads/', 'uploads/'):
        if lower.startswith(prefix):
            return name[len(prefix):]
    return name

def archive_entries(target):
    with zipfile.ZipFile(target) as zf:
        infos = zf.infolist()
        bad = zf.testzip() if False else None  # Deliberately do not stream 2GB to validate CRC
        return {normalize(i.filename): i.file_size for i in infos if not i.is_dir() and '__MACOSX' not in i.filename}

def folder_entries(target):
    files = {}
    for p in target.rglob('*'):
        if p.is_file():
            files[normalize(p.relative_to(target).as_posix())] = p.stat().st_size
    return files

def read_expected(manifest, content_dir):
    expected = {}
    if manifest.is_file():
        with manifest.open(newline='', encoding='utf-8-sig') as fh:
            for row in csv.DictReader(fh):
                name = normalize(row.get('filename', ''))
                if name:
                    expected.setdefault(name, set()).add('WordPress attachment')
    if content_dir.is_dir():
        for f in content_dir.rglob('*'):
            if not f.is_file() or f.suffix.lower() not in ('.md', '.html', '.htm'):
                continue
            body = f.read_text(encoding='utf-8', errors='replace')
            for item in REF.findall(body):
                name = normalize(item.rstrip('.,;'))
                if name:
                    expected.setdefault(name, set()).add('Story image reference')
    return expected

def main():
    parser = argparse.ArgumentParser(description='Check uploaded media against the Off On Our Own WordPress export.')
    parser.add_argument('source', type=Path, help='Path to uploads.zip or extracted wp-content/uploads folder')
    parser.add_argument('--manifest', type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument('--content', type=Path, default=CONTENT)
    parser.add_argument('--output', type=Path, default=Path.cwd() / 'media-audit')
    args = parser.parse_args()
    if not args.source.exists():
        parser.error(f'File or directory not found: {args.source}')
    if not args.manifest.exists():
        parser.error(f'Missing media manifest: {args.manifest}')
    if args.source.is_file() and not zipfile.is_zipfile(args.source):
        parser.error('Source must be a ZIP archive or a directory')
    actual = archive_entries(args.source) if args.source.is_file() else folder_entries(args.source)
    expected = read_expected(args.manifest, args.content)
    folded = {}
    for p in actual:
        folded.setdefault(p.casefold(), []).append(p)
    audit = []
    status_counts = Counter()
    for name, sources in sorted(expected.items()):
        resolved = name if name in actual else next(iter(folded.get(name.casefold(), [])), '')
        status = 'FOUND' if resolved == name else ('CASE_DIFFERENCE' if resolved else 'MISSING')
        status_counts[status] += 1
        audit.append({'expected_path':name,'source':'+'.join(sorted(sources)), 'status':status,
                      'actual_path':resolved, 'size_bytes':actual.get(resolved, '')})
    args.output.mkdir(parents=True, exist_ok=True)
    report_csv = args.output / 'media-audit.csv'
    with report_csv.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=['expected_path','source','status','actual_path','size_bytes'])
        writer.writeheader()
        writer.writerows(audit)
    missing_csv = args.output / 'missing-media.csv'
    with missing_csv.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=['expected_path','source','status','actual_path','size_bytes'])
        writer.writeheader()
        writer.writerows(row for row in audit if row['status'] != 'FOUND')
    summary = {
        'source': str(args.source),
        'zip_or_folder_files':len(actual),
        'uncompressed_media_bytes':sum(actual.values()),
        'total_expected_paths':len(expected),
        'found_exact':status_counts['FOUND'],
        'case_difference':status_counts['CASE_DIFFERENCE'],
        'missing':status_counts['MISSING'],
        'unreferenced_media_files':len(set(actual) - {r['actual_path'] for r in audit if r['actual_path']}),
        'notes':'Manifest covers WordPress attachments and article references. Legacy external Flickr/TravelPod media may still require separate migration.'
    }
    with (args.output / 'media-summary.json').open('w', encoding='utf-8') as fh:
        json.dump(summary, fh, indent=2)
    print(json.dumps(summary, indent=2))
    print(f'\nReports written to: {args.output}')
    return 0 if summary['missing'] == 0 and summary['case_difference'] == 0 else 1

if __name__=='__main__':
    sys.exit(main())
