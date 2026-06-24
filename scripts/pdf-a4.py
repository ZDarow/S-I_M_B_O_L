#!/usr/bin/env python3
"""
Post-processor: convert Letter PDF (612x792) to A4 (595x842).
Uses pikepdf to scale content and resize pages.

Безопасность: использует атомарную запись через временный файл,
чтобы не повредить исходный PDF при сбое.
"""
import logging
import os
import shutil
import sys
import tempfile
from pathlib import Path

from pikepdf import Pdf, Name, Stream

logger = logging.getLogger(__name__)

LETTER_W, LETTER_H = 612.0, 792.0
A4_W, A4_H = 595.276, 841.890  # 210mm × 297mm


def letter_to_a4(in_path: str, out_path: str) -> bool:
    """Сконвертировать Letter PDF в A4 с атомарной записью."""
    if not os.path.exists(in_path):
        logger.error("Input not found: %s", in_path)
        return False

    scale = A4_W / LETTER_W  # 0.972
    offset_y = (A4_H - LETTER_H * scale) / 2

    pdf = Pdf.open(in_path, allow_overwriting_input=True)
    changed = 0
    for page in pdf.pages:
        media = page.MediaBox
        w = float(media[2]) - float(media[0])
        h = float(media[3]) - float(media[1])

        if abs(w - LETTER_W) < 5 and abs(h - LETTER_H) < 5:
            # Build transformation content stream
            content = b"q\n"
            content += f"{scale:.6f} 0 0 {scale:.6f} 0 {offset_y:.6f} cm\n".encode()

            # Collect all existing content streams
            contents = page.Contents
            if isinstance(contents, list):
                for c in contents:
                    content += c.read_bytes()
            elif isinstance(contents, Stream):
                content += contents.read_bytes()
            elif contents is not None:
                try:
                    content += contents.read_bytes()
                except Exception as e:
                    logger.warning("Не удалось прочитать content stream: %s", e)

            content += b"\nQ\n"

            if content:
                page.contents = Stream(pdf, content)

            # Update MediaBox to A4
            page.MediaBox = [0, 0, A4_W, A4_H]

            # Update CropBox if it matches Letter
            if Name.CropBox in page:
                crop = page.CropBox
                if abs(float(crop[2]) - float(crop[0]) - LETTER_W) < 5:
                    page.CropBox = [0, 0, A4_W, A4_H]

            changed += 1

    if changed == 0:
        logger.info("No Letter-size pages found, saving as-is")

    # Атомарная запись через временный файл
    tmp_dir = os.path.dirname(out_path) or "."
    with tempfile.NamedTemporaryFile(
        delete=False, dir=tmp_dir, suffix=".pdf"
    ) as tmp:
        tmp_path = tmp.name

    try:
        pdf.save(tmp_path, compress_streams=True)
        pdf.close()
        shutil.move(tmp_path, out_path)  # атомарная замена
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        pdf.close()
        raise

    # Verify
    pdf2 = Pdf.open(out_path)
    p = pdf2.pages[0]
    w = float(p.MediaBox[2]) / 72 * 25.4
    h = float(p.MediaBox[3]) / 72 * 25.4
    pages = len(pdf2.pages)
    size = os.path.getsize(out_path) / 1024 / 1024
    logger.info("✅ PDF: %d pages, %.0f×%.0f mm, %.1f MB", pages, w, h, size)
    pdf2.close()
    return True


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        stream=sys.stderr,
    )

    proj_root = Path(__file__).resolve().parent.parent
    in_pdf = proj_root / "book" / "book" / "pdf" / "output.pdf"
    out_pdf = in_pdf

    if len(sys.argv) > 1:
        in_pdf = Path(sys.argv[1])
    if len(sys.argv) > 2:
        out_pdf = Path(sys.argv[2])

    letter_to_a4(str(in_pdf), str(out_pdf))
    # Если out_pdf != in_pdf, копируем обратно
    if out_pdf != in_pdf:
        shutil.copy2(str(out_pdf), str(in_pdf))


if __name__ == "__main__":
    main()
