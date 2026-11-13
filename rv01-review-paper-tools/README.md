# review_tools

Small Python tools for the bookkeeping part of a review paper, and for making the explainer videos about it.

**Video:** "Review paper: from search to final draft" (YouTube, channel *Embedded Intelligence Studio*).

## What is in here

| File | What it does |
|---|---|
| `slr.py` | The review-paper tool: `init`, `import`, `dedupe`, `screen`, `number`, `access`, `batches`, `tabs`, `pdfmatch`, `pack`, `cite`, `comments`, `prisma`, `status` |
| `litsearch.py` | Helpers for building search strings |
| `test_slr.py`, `selftest.py` | Tests (`python test_slr.py`, `python selftest.py`) |
| `visuals.py` | Slide images (tables, PRISMA diagram) from CSV/JSON |
| `motion.py`, `motion_build.py` | Animated explainer scenes timed to the narration |
| `clipsync.py` | Re-cuts a screen recording so it follows the narration sentence by sentence |
| `tts.py`, `dry_tts.py`, `voice_api.py`, `voice_match.py` | Narration: your own recordings, a cloned voice through an API, or a silent dry run |
| `build.py` | Joins scenes + narration into `final.mp4` with subtitles |
| `episodes/example/` | The script, slide data and animation definitions used in the first video |

## Quick start (Windows PowerShell, Python 3.10+)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python selftest.py
python test_slr.py

# a review project
python slr.py init my_review --title "My review" --rq "What is known about ..."
#   export your database searches into my_review\01_exports\<database>\ , then:
python slr.py -p my_review import
python slr.py -p my_review dedupe
python slr.py -p my_review screen        # then fill ta_decision in 03_screening\screening.csv
python slr.py -p my_review number
python slr.py -p my_review access        # needs  $env:UNPAYWALL_EMAIL="you@example.org"
python slr.py -p my_review batches       # opens 04_access\index.html
python slr.py -p my_review pdfmatch      # after you drop PDFs into 05_pdfs\inbox
python slr.py -p my_review pack
python slr.py -p my_review cite my_review\07_draft\draft_v01.docx
```

`ffmpeg` must be on the PATH for the video tools.

## Notes

* Download PDFs yourself through your own library access. The tool only opens the pages; it never bulk-downloads from publishers.
* Check your university's and the publishers' rules before uploading papers to any AI tool, and follow your journal's policy on AI use.
* Keys and e-mail addresses are read from environment variables only; nothing is stored in files.

## Licence

MIT (see LICENSE). Fonts in `assets/` are under the SIL Open Font License (see `assets/FONTS-LICENSE.txt`).
