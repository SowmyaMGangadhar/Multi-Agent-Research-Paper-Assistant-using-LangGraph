import os
import re
import fitz
from pathlib import Path
from PIL import Image


class FigureExtractor:

    @staticmethod
    def _safe_name(text):
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"\s+", "_", text)
        return text[:80] or "unknown_paper"

    @staticmethod
    def _compress_image(path, max_size=(1000, 1000), quality=75):
        img = Image.open(path).convert("RGB")
        img.thumbnail(max_size)

        compressed_path = path.replace(".png", "_compressed.jpg")

        img.save(
            compressed_path,
            "JPEG",
            quality=quality,
            optimize=True
        )

        return compressed_path

    @staticmethod
    def _find_caption_blocks(page):
        blocks = page.get_text("blocks")
        captions = []

        for block in blocks:
            x0, y0, x1, y1, text, *_ = block
            text_clean = text.strip()

            if re.match(r"^(Figure|Fig\.)\s*\d+", text_clean, re.IGNORECASE):
                captions.append(
                    {
                        "bbox": (x0, y0, x1, y1),
                        "caption": text_clean
                    }
                )

        return captions

    @staticmethod
    def extract_figures(
        pdf_bytes,
        paper_id="unknown_paper",
        output_base_dir="data/outputs/figures",
        render_scale=2.0
    ):
        paper_id = FigureExtractor._safe_name(paper_id)

        output_dir = os.path.join(output_base_dir, paper_id)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        figures = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_rect = page.rect

            captions = FigureExtractor._find_caption_blocks(page)

            if captions:
                for idx, cap in enumerate(captions):
                    x0, y0, x1, y1 = cap["bbox"]

                    clip = fitz.Rect(
                        0,
                        max(0, y0 - 380),
                        page_rect.width,
                        min(page_rect.height, y1 + 80)
                    )

                    pix = page.get_pixmap(
                        matrix=fitz.Matrix(render_scale, render_scale),
                        clip=clip,
                        alpha=False
                    )

                    file_name = (
                        f"{paper_id}_page_{page_num + 1}_"
                        f"figure_{idx + 1}.png"
                    )

                    raw_path = os.path.join(output_dir, file_name)
                    pix.save(raw_path)

                    compressed_path = FigureExtractor._compress_image(raw_path)

                    figures.append(
                        {
                            "page": page_num + 1,
                            "figure_index": idx + 1,
                            "figure_name": cap["caption"][:120],
                            "path": compressed_path,
                            "raw_path": raw_path,
                            "extension": "jpg",
                            "source": "caption_crop"
                        }
                    )

            else:
                images = page.get_images(full=True)

                for img_index, img in enumerate(images):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)

                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]

                        file_name = (
                            f"{paper_id}_page_{page_num + 1}_"
                            f"image_{img_index + 1}.{image_ext}"
                        )

                        raw_path = os.path.join(output_dir, file_name)

                        with open(raw_path, "wb") as f:
                            f.write(image_bytes)

                        compressed_path = FigureExtractor._compress_image(raw_path)

                        figures.append(
                            {
                                "page": page_num + 1,
                                "figure_index": img_index + 1,
                                "figure_name": f"Image {img_index + 1} on Page {page_num + 1}",
                                "path": compressed_path,
                                "raw_path": raw_path,
                                "extension": "jpg",
                                "source": "embedded_image"
                            }
                        )

                    except Exception:
                        continue

        return figures