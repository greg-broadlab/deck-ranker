import os
import re
import hashlib
from config import PPTX_BASE, CATEGORY_PATTERNS, FOLDER_CATEGORIES, SKIP_DIRS, YEAR_MARKERS, MAX_PER_CATEGORY
from database import upsert_deck


def deck_id(path):
    return hashlib.md5(path.encode()).hexdigest()[:12]


def categorize(path, filename):
    folder = path.lower()
    for cat, patterns in FOLDER_CATEGORIES.items():
        if any(p in folder for p in patterns):
            return cat
    name = filename.lower()
    for cat, patterns in CATEGORY_PATTERNS.items():
        if any(p in name for p in patterns):
            return cat
    return None


def should_skip(dirname):
    return any(s in dirname.lower() for s in SKIP_DIRS)


def is_recent_deck(filename):
    name = filename.lower()
    return any(m in name for m in YEAR_MARKERS)


def long(path):
    return '\\\\?\\' + path if not path.startswith('\\\\?\\') else path


def get_mtime(path):
    try:
        return os.path.getmtime(long(path))
    except OSError:
        return 0


def base_name(filename):
    """Strip version suffix to group versions of the same deck together."""
    name = os.path.splitext(filename)[0]
    # Remove trailing: v2, v3, _v2, - v2, (v2), copy, final, etc.
    name = re.sub(r'[\s_\-]+v\d+\s*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[\s_\-]+(copy|final|draft|updated?|revised?)\d*\s*$', '', name, flags=re.IGNORECASE)
    return name.strip().lower()


def version_number(filename):
    """Extract version number for sorting (higher = more recent)."""
    match = re.search(r'[\s_\-]+v(\d+)\s*$', os.path.splitext(filename)[0], flags=re.IGNORECASE)
    return int(match.group(1)) if match else 0


def dedup_versions(items):
    """Keep only the latest version of each unique deck."""
    groups = {}
    for item in items:
        mtime, path, filename = item
        key = base_name(filename)
        existing = groups.get(key)
        if not existing:
            groups[key] = item
        else:
            # Prefer higher version number, then newer mtime
            if version_number(filename) > version_number(existing[2]) or (
                version_number(filename) == version_number(existing[2]) and mtime > existing[0]
            ):
                groups[key] = item
    return list(groups.values())


def scan():
    found = {}

    for root, dirs, files in os.walk(PPTX_BASE):
        dirs[:] = [d for d in dirs if not should_skip(d)]
        for file in files:
            if not file.lower().endswith('.pptx') or file.startswith('~$'):
                continue
            category = categorize(os.path.join(root, file), file)
            if not category:
                continue
            if not is_recent_deck(file):
                continue
            path = os.path.join(root, file)
            mtime = get_mtime(path)
            found.setdefault(category, []).append((mtime, path, file))

    count = 0
    for category, items in found.items():
        # Deduplicate versions first, then sort by recency, then cap
        unique = dedup_versions(items)
        unique.sort(key=lambda x: x[0], reverse=True)
        for mtime, path, file in unique[:MAX_PER_CATEGORY]:
            did = deck_id(path)
            upsert_deck(did, long(path), file, category)
            count += 1

    return count
