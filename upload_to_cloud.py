# Run this once to render all decks and upload to Cloudinary + Supabase.
# Safe to re-run -- skips already-uploaded slides.
# Usage: cd deck-ranker && python upload_to_cloud.py

import os
import sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

import cloudinary
import cloudinary.uploader
import cloudinary.api
from supabase import create_client
from database import get_decks_by_category, init_db
from scanner import scan
from renderer import render_deck, get_slide_count, get_cache_dir, get_slide_path
from config import CATEGORIES

cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET'),
)

sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))


def cloudinary_url(prefix, slide_num):
    return f"https://res.cloudinary.com/{os.getenv('CLOUDINARY_CLOUD_NAME')}/image/upload/{prefix}/{slide_num}.png"


def slide_already_uploaded(prefix, slide_num):
    try:
        cloudinary.api.resource(f"{prefix}/{slide_num}")
        return True
    except cloudinary.exceptions.NotFound:
        return False
    except Exception:
        return False


def upload_deck(deck):
    deck_id = deck['id']
    category = deck['category']
    prefix = f"deck-ranker/{category}/{deck_id}"

    # Render locally if not done yet
    if get_slide_count(deck_id) == 0:
        print(f"    Rendering slides...")
        try:
            render_deck(deck_id, deck['path'])
        except Exception as e:
            print(f"    Render failed: {e}")
            return False

    slide_count = get_slide_count(deck_id)
    if slide_count == 0:
        print(f"    No slides found, skipping")
        return False

    # Upload slides to Cloudinary
    uploaded = 0
    skipped = 0
    for i in range(slide_count):
        path = get_slide_path(deck_id, i)
        if not os.path.exists(path):
            continue
        try:
            cloudinary.uploader.upload(
                path,
                public_id=f"{prefix}/{i}",
                overwrite=False,
                resource_type="image",
                folder="",
            )
            uploaded += 1
        except Exception as e:
            if "already exists" in str(e).lower() or "overwrite" in str(e).lower():
                skipped += 1
            else:
                print(f"    Slide {i} error: {e}")

    print(f"    {uploaded} uploaded, {skipped} already existed — {slide_count} total slides")

    # Upsert to Supabase
    sb.table('decks').upsert({
        'id': deck_id,
        'filename': deck['filename'],
        'category': category,
        'elo': deck['elo'],
        'matches': deck['matches'],
        'slide_count': slide_count,
        'cloudinary_prefix': prefix,
    }).execute()

    return True


def main():
    print("Deck Ranker — Cloud Upload")
    print("=" * 40)

    init_db()
    print("Scanning for decks...")
    total_found = scan()
    print(f"Found {total_found} decks across {len(CATEGORIES)} categories\n")

    grand_total = 0
    for cat_id, cat_name in CATEGORIES.items():
        decks = get_decks_by_category(cat_id)
        print(f"── {cat_name} ({len(decks)} decks)")
        success = 0
        for i, deck in enumerate(decks):
            print(f"  [{i+1}/{len(decks)}] {deck['filename']}")
            if upload_deck(deck):
                success += 1
        print(f"  Done: {success}/{len(decks)} uploaded\n")
        grand_total += success

    print("=" * 40)
    print(f"Complete — {grand_total} decks in Cloudinary + Supabase")
    print(f"Now deploy the frontend/ folder to Amplify")


if __name__ == '__main__':
    main()
