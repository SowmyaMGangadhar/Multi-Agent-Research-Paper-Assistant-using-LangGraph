import fitz

import numpy as np

from sklearn.cluster import KMeans


class PDFParser:

    @staticmethod
    def extract_blocks(page, page_num):

        raw = page.get_text("dict")

        blocks = []

        for block in raw["blocks"]:

            if "lines" not in block:
                continue

            text = []

            sizes = []

            bold = False

            for line in block["lines"]:
                for span in line["spans"]:

                    t = span["text"].strip()

                    if not t:
                        continue

                    text.append(t)
                    sizes.append(span["size"])

                    if "bold" in span["font"].lower():
                        bold = True

            full_text = " ".join(text).strip()

            if not full_text:
                continue

            x0, y0, x1, y1 = block["bbox"]

            center_x = (x0 + x1) / 2

            blocks.append({
                "text": full_text,
                "font_size": float(np.mean(sizes)),
                "is_bold": bold,
                "bbox": block["bbox"],
                "center_x": center_x,
                "y": y0,
                "page": page_num
            })

        return blocks

    @staticmethod
    def detect_columns(blocks):

        if len(blocks) < 10:
            return 1, blocks

        xs = np.array([[b["center_x"]] for b in blocks])

        k = 2

        kmeans = KMeans(
            n_clusters=k,
            n_init=10,
            random_state=0
        ).fit(xs)

        labels = kmeans.labels_

        left = sum(labels == 0)

        right = sum(labels == 1)

        if min(left, right) < 3:
            return 1, blocks

        for i, b in enumerate(blocks):
            b["cluster"] = int(labels[i])

        return 2, blocks

    @staticmethod
    def sort_blocks(blocks, n_columns):

        if n_columns == 1:
            return sorted(blocks, key=lambda b: (b["y"], b["center_x"]))

        cluster_0 = [b for b in blocks if b["cluster"] == 0]
        cluster_1 = [b for b in blocks if b["cluster"] == 1]

        mean_x_0 = sum(b["center_x"] for b in cluster_0) / len(cluster_0)
        mean_x_1 = sum(b["center_x"] for b in cluster_1) / len(cluster_1)

        if mean_x_0 <= mean_x_1:
            left, right = cluster_0, cluster_1
        else:
            left, right = cluster_1, cluster_0

        page_width = max(b["bbox"][2] for b in blocks)

        full_width = []

        left_only = []

        right_only = []

        for b in blocks:

            x0, _, x1, _ = b["bbox"]

            width_ratio = (x1 - x0) / page_width

            if width_ratio > 0.7:
                full_width.append(b)
            elif b in left:
                left_only.append(b)
            else:
                right_only.append(b)

        full_width = sorted(full_width, key=lambda b: b["y"])
        left_only = sorted(left_only, key=lambda b: b["y"])
        right_only = sorted(right_only, key=lambda b: b["y"])

        result = []

        consumed = set()

        for fw in full_width:

            while left_only and left_only[0]["y"] < fw["y"]:
                result.append(left_only.pop(0))

            while right_only and right_only[0]["y"] < fw["y"]:
                result.append(right_only.pop(0))

            result.append(fw)

        result.extend(left_only)
        result.extend(right_only)

        return result

    @staticmethod
    def extract_text_blocks(pdf_source):

        if isinstance(pdf_source, bytes):
            doc = fitz.open(stream=pdf_source, filetype="pdf")
        else:
            doc = fitz.open(pdf_source)

        all_blocks = []

        font_sizes = []

        for page_num in range(len(doc)):

            page = doc[page_num]

            blocks = PDFParser.extract_blocks(page, page_num)
            
            n_cols, blocks = PDFParser.detect_columns(blocks)

            blocks = PDFParser.sort_blocks(blocks, n_cols)
            for order, b in enumerate(blocks):
                b["reading_order"] = order

            for b in blocks:
                font_sizes.append(b["font_size"])

            all_blocks.extend(blocks)

        avg_font = np.median(font_sizes) if font_sizes else 10

        return {
            "blocks": all_blocks,
            "avg_font_size": avg_font
        }

