# Broadlab Deck Ranker — Project Handoff

## What this is

An internal tool that ranks Broadlab's slide decks using an ELO system (same algorithm chess uses). Two decks are shown side by side, someone picks the better one, scores update. Over time the best decks rise to the top.

The goal is not just ranking — it's building a knowledge base of what "good" looks like at Broadlab. The top-ranked decks per category will feed into a Claude Design system so that future decks are built from real examples of the best work, not from scratch.

---

## The two phases

**Phase 1 — Local tool (complete)**
A Flask app running locally at `http://127.0.0.1:5050`. Renders PPTX slides using LibreOffice (installed portably at `C:\Users\GregBrenner\LibreOffice\`), stores rankings in SQLite, serves slides from a local cache. Used by Greg to run initial comparisons.

**Phase 2 — Cloud tool (in progress)**
The same tool rebuilt as a static frontend (no backend server) that runs for the whole exec team via Amplify. Slides stored in Cloudinary, rankings stored in Supabase. The upload script (`upload_to_cloud.py`) renders all decks locally and pushes them to the cloud. Frontend lives in `frontend/`.

---

## Architecture

### Local (Phase 1)
```
app.py          Flask server
database.py     SQLite (data/rankings.db)
scanner.py      Walks OneDrive folder, finds PPTX files
renderer.py     LibreOffice → PDF → PNG via pymupdf
elo.py          ELO calculation (K=32)
scorer.py       Claude-powered quality filter (optional)
config.py       All settings live here
```

### Cloud (Phase 2)
```
upload_to_cloud.py      One-time script: renders all decks, uploads to Cloudinary + Supabase
frontend/
  index.html            Home page — category cards with top 5 rankings
  compare.html          Side-by-side comparison, vote submission
  rankings.html         Full leaderboard per category
  config.js             Supabase + Cloudinary credentials, ELO logic, shared helpers
  style.css             Full stylesheet (Broadlab brand — teal, Inter font)
```

---

## Deck categories

| ID | Name | How it's found |
|---|---|---|
| intro | Intro | Files inside `Business Development/BL Presentations/` folder |
| rtb | RTB | "rtb" in filename |
| optimisation | Optimisation | "optim" in filename |
| eoc | EOC | "eoc" in filename |
| qbr | QBR | "qbr" in filename |

All configured in `config.py`. Year filter: only 2025–2026 decks. Cap: 60 per category. Version dedup: if v1/v2/v3 of same deck exist, only keep the latest.

---

## Credentials

All credentials are in `.env` (never commit this):
- `SUPABASE_URL` — `https://kznfnzhttmgidgicjeyx.supabase.co`
- `SUPABASE_ANON_KEY` — JWT anon key (safe to expose in frontend JS)
- `SUPABASE_DB_PASSWORD` — keep private, used for direct DB connections only
- `CLOUDINARY_CLOUD_NAME` — `dtm0s452r`
- `CLOUDINARY_API_KEY` / `CLOUDINARY_API_SECRET` — for upload script only

Credentials are also hardcoded in `frontend/config.js` (anon key only — this is intentional and safe by Supabase design).

---

## Database schema (Supabase)

```sql
decks        — id, filename, category, elo, matches, slide_count, cloudinary_prefix
comparisons  — id, category, winner_id, loser_id, created_at
```

RLS is enabled with open read/write policies (internal tool, no auth needed for now).

---

## Current state

- [x] Local Flask app working (Phase 1 complete)
- [x] 5 categories scanning and rendering correctly
- [x] Supabase tables created
- [x] Cloudinary account connected
- [x] `upload_to_cloud.py` built and tested
- [x] Static frontend built (`frontend/`)
- [ ] Upload script finished running (may still be in progress)
- [ ] Frontend deployed to Amplify

---

## What needs to happen next

### 1. Verify the upload completed
Run this to check how many decks made it to Supabase:
```
cd C:\Users\GregBrenner\deck-ranker
python -c "
from dotenv import load_dotenv; load_dotenv()
from supabase import create_client
import os
sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
r = sb.table('decks').select('category', count='exact').execute()
print(r.data[:10])
"
```

### 2. Deploy frontend to Amplify
The `frontend/` folder is a self-contained static site — no build step needed.
- Go to AWS Amplify console
- Create new app → deploy without Git → drag and drop the `frontend/` folder
- That's the URL you share with the exec team

### 3. Exec team uses the compare page
Share the Amplify URL. Anyone on the team opens it, picks a category, and starts comparing. Every vote writes directly to Supabase. Rankings update in real time for everyone.

### 4. AI quality filter (optional, run locally)
Once rankings have settled, use the "AI filter" button in the local Flask app to have Claude remove low-quality decks from the pool. Requires an Anthropic API key.

### 5. Export top decks for the design system
Once the top 5 per category are identified, those deck slides can be exported and uploaded to a Claude Project as the foundation of Broadlab's slide design system. This is the long-term goal — the ranker feeds the design system.

---

## How to run the local tool

```bash
cd C:\Users\GregBrenner\deck-ranker
python app.py
# opens at http://127.0.0.1:5050
# network URL printed on startup for team access over office WiFi
```

## How to run the upload script

```bash
cd C:\Users\GregBrenner\deck-ranker
python upload_to_cloud.py
# renders all decks with LibreOffice, uploads to Cloudinary, saves to Supabase
# safe to re-run — skips already-uploaded slides
```

---

## Key paths

| What | Where |
|---|---|
| PPTX source files | `C:\Users\GregBrenner\Broadlab\Broadlab - NEW STRUCTURE - Documents\` |
| LibreOffice (portable) | `C:\Users\GregBrenner\LibreOffice\program\soffice.exe` |
| Local slide cache | `C:\Users\GregBrenner\deck-ranker\cache\` |
| Local database | `C:\Users\GregBrenner\deck-ranker\data\rankings.db` |
| Frontend | `C:\Users\GregBrenner\deck-ranker\frontend\` |
| Credentials | `C:\Users\GregBrenner\deck-ranker\.env` |

---

## Important notes

- The local Flask app and the cloud frontend share the same deck IDs (MD5 hash of file path) so data is consistent
- LibreOffice was installed portably (no admin required) by extracting the MSI to `C:\Users\GregBrenner\LibreOffice\`
- The upload script marks slides as `overwrite=False` in Cloudinary — safe to re-run without duplicate charges
- ELO starts at 1000, K=32. Rankings only become reliable after ~200 comparisons per category
- The `frontend/` folder is pure HTML/JS/CSS — no build step, no Node, no npm. Just drag and drop to Amplify
