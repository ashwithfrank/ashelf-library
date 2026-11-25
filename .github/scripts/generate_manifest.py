#!/usr/bin/env python3
"""Builds manifest.json for the Ashelf library. Run from the repo root."""
import json, os, re, subprocess
from urllib.parse import quote

OWNER, REPO = 'ashwithfrank', 'ashelf-library'
PAGES = f'https://{OWNER}.github.io/{REPO}'
RAW = f'https://raw.githubusercontent.com/{OWNER}/{REPO}/main'
VROOT = 'library'  # virtual root: the site and app navigate paths under it
EXCLUDED = {'manifest.json', 'README.md', 'readme.md', 'LICENSE', 'index.html'}
TYPES = {
    'pdf': ['pdf'],
    'doc': ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'odt', 'ods', 'odp', 'txt', 'csv', 'rtf'],
    'image': ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'ico', 'tiff', 'avif'],
    'video': ['mp4', 'webm', 'ogv', 'mov', 'avi', 'mkv', 'm4v'],
    'audio': ['mp3', 'wav', 'ogg', 'aac', 'flac', 'm4a', 'opus'],
}
TYPOS = {'Descrete': 'Discrete', 'Enlish': 'English'}
PREFIX = re.compile(r'^SEP\s*(?:BCA)?[\s-]*[IVX]+\s*SEM\s*[-–]?\s*', re.I)
YEAR = re.compile(r'^\d{4}-\d{2}$')


def file_type(ext):
    return next((t for t, exts in TYPES.items() if ext in exts), 'other')


def classify(folders, name):
    if 'question papers' in [f.lower() for f in folders]:
        return 'question_paper'
    n = name.lower()
    if 'record' in n:
        return 'record'
    if 'question bank' in n or re.search(r'\bqb\b', n):
        return 'question_bank'
    return 'notes'


def make_title(stem, category):
    t = re.sub(r'[_\s]+', ' ', stem).strip()
    if category == 'question_paper':
        t = PREFIX.sub('', t).strip(' -–') or t
    for wrong, right in TYPOS.items():
        t = t.replace(wrong, right)
    return t


def modified(path):
    out = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', path],
                         capture_output=True, text=True).stdout.strip()
    return out or None


entries = []
for root, dirs, files in os.walk('.'):
    dirs[:] = sorted(d for d in dirs if not d.startswith('.'))
    rel_root = os.path.relpath(root, '.').replace('\\', '/')
    if rel_root != '.':
        entries.append({'kind': 'folder', 'name': os.path.basename(rel_root),
                        'path': f'{VROOT}/{rel_root}'})
    for fname in sorted(files):
        if fname in EXCLUDED or fname.startswith('.'):
            continue
        rel = fname if rel_root == '.' else f'{rel_root}/{fname}'
        folders = [] if rel_root == '.' else rel_root.split('/')
        stem, dot, ext = fname.rpartition('.')
        if not dot:
            stem, ext = fname, ''
        ext = ext.lower()
        category = classify(folders, fname)
        sem = next((i for i, f in enumerate(folders) if re.match(r'^SEM\b', f, re.I)), None)
        subject = None
        if sem is not None and sem + 1 < len(folders) and category != 'question_paper':
            subject = folders[sem + 1]
        entries.append({
            'kind': 'file', 'name': fname, 'path': f'{VROOT}/{rel}',
            'ext': ext, 'type': file_type(ext), 'size': os.path.getsize(rel),
            'url': f'{PAGES}/{quote(rel)}', 'dlUrl': f'{RAW}/{quote(rel)}',
            'title': make_title(stem, category), 'category': category,
            'semester': folders[sem] if sem is not None else None,
            'subject': subject,
            'year': next((f for f in folders if YEAR.match(f)), None),
            'modified': modified(rel),
        })

with open('manifest.json', 'w', encoding='utf-8') as f:
    json.dump(entries, f, ensure_ascii=False, separators=(',', ':'))
print(f'Generated manifest.json with {len(entries)} entries')
