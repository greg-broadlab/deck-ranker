import os
import subprocess
import fitz
from config import CACHE_DIR, SOFFICE


def get_cache_dir(deck_id):
    return os.path.join(CACHE_DIR, deck_id)


def get_slide_count(deck_id):
    d = get_cache_dir(deck_id)
    if not os.path.exists(d):
        return 0
    return len([f for f in os.listdir(d) if f.endswith('.png')])


def is_rendered(deck_id):
    return get_slide_count(deck_id) > 0


def get_slide_path(deck_id, slide_num):
    return os.path.join(CACHE_DIR, deck_id, f"{slide_num}.png")


def render_deck(deck_id, pptx_path):
    cache_dir = get_cache_dir(deck_id)
    os.makedirs(cache_dir, exist_ok=True)

    pdf_path = os.path.join(cache_dir, "slides.pdf")
    subprocess.run(
        [SOFFICE, "--headless", "--convert-to", "pdf", "--outdir", cache_dir, pptx_path],
        capture_output=True, timeout=120
    )

    # LibreOffice names the PDF after the source file — find it
    if not os.path.exists(pdf_path):
        pdfs = [f for f in os.listdir(cache_dir) if f.endswith('.pdf')]
        if not pdfs:
            raise RuntimeError("LibreOffice produced no PDF output")
        os.rename(os.path.join(cache_dir, pdfs[0]), pdf_path)

    doc = fitz.open(pdf_path)
    slide_count = len(doc)
    mat = fitz.Matrix(2.0, 2.0)
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=mat)
        pix.save(os.path.join(cache_dir, f"{i}.png"))
    doc.close()

    return slide_count
