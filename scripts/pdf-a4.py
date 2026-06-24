#!/usr/bin/env python3
"""
Post-processor: convert Letter PDF (612x792) to A4 (595x842).
Uses pikepdf to scale content and resize pages.
"""
import sys, os
from pikepdf import Pdf, Page, Rectangle, Name, Stream
from pathlib import Path

LETTER_W, LETTER_H = 612.0, 792.0
A4_W, A4_H = 595.276, 841.890  # 210mm × 297mm

def letter_to_a4(in_path: str, out_path: str) -> bool:
    if not os.path.exists(in_path):
        print(f"Input not found: {in_path}", file=sys.stderr)
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
                except:
                    pass

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
        print("No Letter-size pages found, saving as-is", file=sys.stderr)

    pdf.save(out_path, compress_streams=True)
    pdf.close()

    # Verify
    pdf2 = Pdf.open(out_path)
    p = pdf2.pages[0]
    w = float(p.MediaBox[2]) / 72 * 25.4
    h = float(p.MediaBox[3]) / 72 * 25.4
    pages = len(pdf2.pages)
    size = os.path.getsize(out_path) / 1024 / 1024
    print(f"✅ PDF: {pages} pages, {w:.0f}×{h:.0f} mm, {size:.1f} MB")
    pdf2.close()
    return True


if __name__ == "__main__":
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
        import shutil
        shutil.copy2(str(out_pdf), str(in_pdf))
