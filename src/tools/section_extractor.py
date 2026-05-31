import re
import numpy as np
from collections import Counter


class SectionExtractor:

    @staticmethod
    def clean(text):
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def normalize_spaced_caps(text):
        prev = None
        while prev != text:
            prev = text
            text = re.sub(
                r'\b([A-Z])\s+([A-Za-z]{2,})\b',
                lambda m: (m.group(1) + m.group(2)).upper(),
                text
            )
        text = re.sub(r'\s*-\s*', '-', text)
        return text

    @staticmethod
    def is_heading(block, font_rank_threshold=0.85):

        raw_text = SectionExtractor.clean(block["text"])
        text = SectionExtractor.normalize_spaced_caps(raw_text)

        if len(text) == 0:
            return False

        if len(text.split()) > 12:
            return False

        if text.endswith((".", ",", ";", ":")):
            return False

        digit_ratio = sum(c.isdigit() for c in text) / max(len(text), 1)
        if digit_ratio > 0.25:
            return False

        lowered = text.lower()
        if any(x in lowered for x in ["et al", "doi", "arxiv", "proceedings"]):
            return False

        score = 0

        if re.match(r"^\d+\s+[A-Z]", text):
            score += 3

        is_subheading = bool(re.match(r"^\d+\.\d+(\.\d+)?\s+[A-Za-z]", text))
        if is_subheading:
            score += 3

        if lowered in {
            "abstract", "introduction",
            "experiments", "results", "conclusion", "references"
        } and block["font_rank"] >= 0.85:
            return 5

        if block["font_rank"] >= font_rank_threshold:
            score += 4

        if is_subheading and block["font_rank"] >= 0.60:
            score += 1

        if block.get("is_bold", False):
            score += 2

        if is_subheading:
            return score >= 3

        return score >= 4

    @staticmethod
    def extract_sections(parsed):

        blocks = parsed["blocks"]

        font_sizes = np.array([b["font_size"] for b in blocks])
        sorted_sizes = np.sort(font_sizes)

        for b in blocks:
            rank = np.searchsorted(sorted_sizes, b["font_size"]) / len(sorted_sizes)
            b["font_rank"] = rank

        page_height = 842.0
        for b in blocks:
            b["global_pos"] = b["page"] * page_height + b["y"]

        # print("\nDETECTED HEADINGS:\n")

        headings = []
        for b in blocks:
            if SectionExtractor.is_heading(b):
                # print(SectionExtractor.normalize_spaced_caps(SectionExtractor.clean(b["text"])))
                headings.append(b)

        sections = {}
        heading_positions = []

        for b in blocks:
            if SectionExtractor.is_heading(b):
                key = SectionExtractor.normalize_spaced_caps(SectionExtractor.clean(b["text"]))
                sections[key] = ""
                heading_positions.append({
                    "key": key,
                    "global_pos": b["global_pos"]
                })

        heading_positions = sorted(heading_positions, key=lambda h: h["global_pos"])

        for b in blocks:

            if SectionExtractor.is_heading(b):
                continue

            block_pos = b["global_pos"]

            current = None
            for i, h in enumerate(heading_positions):

                if block_pos <= h["global_pos"]:
                    break

                if i + 1 < len(heading_positions):
                    if block_pos < heading_positions[i + 1]["global_pos"]:
                        current = h["key"]
                        break
                else:
                    current = h["key"]

            if current:
                sections[current] += b["text"] + " "

        return sections





