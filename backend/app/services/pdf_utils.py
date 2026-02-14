from typing import List
from PIL import Image
import io


def pdf_to_images(pdf_bytes: bytes, dpi: int = 200) -> List[Image.Image]:
    try:
        import fitz
    except ImportError:
        raise RuntimeError("PyMuPDF is not installed. Run: pip install PyMuPDF")

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images: List[Image.Image] = []
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    for page in doc:
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        if img.mode != "RGB":
            img = img.convert("RGB")
        images.append(img)

    doc.close()
    return images


def pdf_page_count(pdf_bytes: bytes) -> int:
    try:
        import fitz
    except ImportError:
        raise RuntimeError("PyMuPDF is not installed. Run: pip install PyMuPDF")

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    count = len(doc)
    doc.close()
    return count


def svg_to_image(svg_bytes: bytes, min_long_side: int = 3000) -> Image.Image:
    try:
        import cairosvg
    except ImportError:
        raise RuntimeError("cairosvg is not installed. Run: pip install cairosvg")

    probe = cairosvg.svg2png(bytestring=svg_bytes)
    probe_img = Image.open(io.BytesIO(probe))
    nat_w, nat_h = probe_img.size

    scale = max(1.0, min_long_side / max(nat_w, nat_h))
    out_w = int(nat_w * scale)
    out_h = int(nat_h * scale)

    png_data = cairosvg.svg2png(
        bytestring=svg_bytes,
        output_width=out_w,
        output_height=out_h,
        background_color="white",
    )
    img = Image.open(io.BytesIO(png_data))

    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")

    print(f"   SVG rendered: native={nat_w}x{nat_h}, output={img.size[0]}x{img.size[1]}, scale={scale:.2f}")
    return img

