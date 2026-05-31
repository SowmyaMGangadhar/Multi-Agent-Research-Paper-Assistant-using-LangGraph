import fitz
import re


MATH_FONT_PATTERNS = [
    "cmsy", "cmex", "cmmi", "cmmib", "cmr",
    "msam", "msbm", "eufm", "eurm",
    "stix", "xits", "mathtime", "mtsy",
    "mtmi", "mt-", "txsy", "pxsy",
]

MATH_UNICODE_RANGES = [
    (0x0391, 0x03C9),
    (0x2200, 0x22FF),
    (0x1D400, 0x1D7FF),
    (0x2100, 0x214F),
    (0x27C0, 0x27EF),
    (0x2980, 0x29FF),
]

DISPLAY_EQ_RE = re.compile(
    r"^("
    r"[A-Za-z_]+\s*[\(\[{]"
    r"|[A-Za-z_]+\s*=\s*"
    r"|[A-Za-z_]\s*_\s*[\{0-9]"
    r"|[A-Za-z_]\s*\^\s*[\{0-9\-\(]"
    r"|\\[a-zA-Z]+"
    r"|[∑∏∫∂∇√±×÷⊗⊕]"
    r"|[0-9]+\s*[=<>]"
    r")"
)

NOISE_WORDS = re.compile(
    r"\b(et al|doi|arxiv|proceedings|university|google|email|gmail|"
    r"http|www|copyright|figure|table|section|chapter|page|equal "
    r"contribution|work performed)\b",
    re.IGNORECASE
)


def _is_math_font(font_name):
    fn = font_name.lower()
    return any(p in fn for p in MATH_FONT_PATTERNS)


def _has_math_unicode(ch):
    cp = ord(ch)
    for lo, hi in MATH_UNICODE_RANGES:
        if lo <= cp <= hi:
            return True
    return False


def _math_char_ratio(text):
    if not text:
        return 0.0
    math_count = sum(
        1 for ch in text
        if _has_math_unicode(ch)
        or ch in "=^_{}∑∏∫∂∇∞√±×÷⊗⊕≤≥≠∝∈∉⊂⊃∩∪"
    )
    return math_count / len(text)


def _math_font_ratio(block):
    math_chars = 0
    total_chars = 0
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            t = span.get("text", "")
            if not t.strip():
                continue
            n = len(t)
            total_chars += n
            if _is_math_font(span.get("font", "")):
                math_chars += n
    if total_chars == 0:
        return 0.0
    return math_chars / total_chars


def _block_text_and_words(block):
    parts = []
    for line in block.get("lines", []):
        line_parts = []
        for span in line.get("spans", []):
            t = span.get("text", "").strip()
            if t:
                line_parts.append(t)
        if line_parts:
            parts.append(" ".join(line_parts))
    full = "\n".join(parts)
    words = full.split()
    return full, words


def _is_centered(block, page_width):
    x0, _, x1, _ = block["bbox"]
    block_center = (x0 + x1) / 2
    page_center = page_width / 2
    return abs(block_center - page_center) < page_width * 0.15


def _score_block(block, page_width):

    if "text" in block:
        text = block["text"]
        words = text.split()
    else:
        text, words = _block_text_and_words(block)
    if _looks_like_author_block(text):
        return 0, text
    if not text.strip():
        return 0, text

    word_count = len(words)

    if NOISE_WORDS.search(text):
        return 0, text

    if word_count > 40:
        return 0, text

    score = 0

    mfr = _math_font_ratio(block)
    if mfr >= 0.8:
        score += 8
    elif mfr >= 0.5:
        score += 5
    elif mfr >= 0.2:
        score += 2

    mcr = _math_char_ratio(text)
    if mcr >= 0.3:
        score += 6
    elif mcr >= 0.15:
        score += 3
    elif mcr >= 0.05:
        score += 1

    first_line = words[0] if words else ""
    if DISPLAY_EQ_RE.match(first_line):
        score += 3

    if word_count <= 15 and score >= 4:
        score += 2

    if word_count <= 6 and score >= 3:
        score += 2

    if _is_centered(block, page_width):
        score += 1

    if word_count > 20:
        score -= 3

    if word_count > 30:
        score -= 3

    return score, text
def _looks_like_author_block(text):

    lower = text.lower()

    if "@" in text:
        return True

    author_keywords = [
        "google",
        "research",
        "brain",
        "university",
        "institute",
        "department",
        ".edu"
    ]

    if any(k in lower for k in author_keywords):
        return True

    lines = [x.strip() for x in text.split("\n") if x.strip()]

    if len(lines) <= 4:

        capitalized = 0

        words = text.split()

        for w in words:
            if len(w) > 1 and w[0].isupper():
                capitalized += 1

        if len(words) > 0:
            ratio = capitalized / len(words)

            if ratio > 0.8:
                return True

    return False
def _merge_neighboring_blocks(blocks):

    if not blocks:
        return []

    blocks = sorted(
        blocks,
        key=lambda b: (
            b["bbox"][1],
            b["bbox"][0]
        )
    )

    merged = []
    used = set()

    for i, current in enumerate(blocks):

        if i in used:
            continue

        x0a, y0a, x1a, y1a = current["bbox"]

        merged_text = current["text"]

        merged_bbox = list(current["bbox"])

        for j in range(i + 1, len(blocks)):

            if j in used:
                continue

            nxt = blocks[j]

            x0b, y0b, x1b, y1b = nxt["bbox"]

            same_line = abs(y0a - y0b) < 15

            horizontal_gap = x0b - x1a

            if same_line and horizontal_gap < 250:

                merged_text += " " + nxt["text"]

                merged_bbox[0] = min(merged_bbox[0], x0b)
                merged_bbox[1] = min(merged_bbox[1], y0b)
                merged_bbox[2] = max(merged_bbox[2], x1b)
                merged_bbox[3] = max(merged_bbox[3], y1b)

                used.add(j)

        current["text"] = merged_text
        current["bbox"] = tuple(merged_bbox)

        merged.append(current)

    return merged


class EquationExtractor:

    @staticmethod
    def extract_equations(pdf_source, score_threshold=5):
        if isinstance(pdf_source, bytes):
            doc = fitz.open(stream=pdf_source, filetype="pdf")
        else:
            doc = fitz.open(pdf_source)

        results = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_width = page.rect.width
            raw = page.get_text("dict")

            candidate_blocks = []

            for block in raw.get("blocks", []):

                if "lines" not in block:
                    continue

                score, text = _score_block(
                    block,
                    page_width
                )

                if score < 5:
                    continue

                block["text"] = text
                block["score"] = score

                candidate_blocks.append(block)

            candidate_blocks = _merge_neighboring_blocks(
                candidate_blocks
            )

            for block in candidate_blocks:

                score, text = _score_block(
                    block,
                    page_width
                )

                if score < score_threshold:
                    continue

                results.append({
                    "page": page_num,
                    "bbox": tuple(block["bbox"]),
                    "text": text,
                    "score": score
                })

                

        return results