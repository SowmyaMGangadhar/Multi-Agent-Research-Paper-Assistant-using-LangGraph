import re
from difflib import SequenceMatcher


class PaperValidator:

    @staticmethod
    def is_arxiv_id(text: str) -> bool:
        return re.search(r"\b\d{4}\.\d{4,5}(v\d+)?\b", text or "") is not None

    @staticmethod
    def is_url(text: str) -> bool:
        return bool(re.search(r"https?://\S+", text or ""))

    @staticmethod
    def is_probably_garbage(query: str) -> bool:
        if not query or not query.strip():
            return True

        query = query.strip()

        if len(query) < 3:
            return True

        words = query.split()

        if len(words) == 1 and not PaperValidator.is_arxiv_id(query):
            return True

        alpha_chars = sum(c.isalpha() for c in query)
        total_chars = len(query)

        if total_chars > 0 and alpha_chars / total_chars < 0.35:
            if not PaperValidator.is_arxiv_id(query) and not PaperValidator.is_url(query):
                return True

        return False

    @staticmethod
    def similarity(a: str, b: str) -> float:
        a = (a or "").lower().strip()
        b = (b or "").lower().strip()

        return SequenceMatcher(None, a, b).ratio()

    @staticmethod
    def validate_result(query: str, paper: dict) -> bool:
        if not paper:
            return False

        if PaperValidator.is_arxiv_id(query):
            return True

        if PaperValidator.is_url(query):
            return True

        title = paper.get("title", "")

        if not title:
            return False

        score = PaperValidator.similarity(query, title)

        query_words = set(query.lower().split())
        title_words = set(title.lower().split())

        overlap = len(query_words.intersection(title_words)) / max(len(query_words), 1)

        if score >= 0.45:
            return True

        if overlap >= 0.45:
            return True

        return False