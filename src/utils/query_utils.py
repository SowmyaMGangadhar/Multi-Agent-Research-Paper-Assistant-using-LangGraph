import re


ARXIV_ID_RE = r"\b\d{4}\.\d{4,5}(v\d+)?\b"
URL_RE = r"https?://\S+"


QUESTION_TRIGGERS = [
    "can you",
    "could you",
    "please",
    "summarize",
    "summerize",
    "explain",
    "tell me",
    "what is",
    "what are",
    "how",
    "why",
    "in points",
    "in few lines",
    "in few sentences",
    "math",
    "equation",
    "intuition",
]


def extract_arxiv_id(text: str):
    match = re.search(ARXIV_ID_RE, text)
    return match.group(0) if match else None


def extract_url(text: str):
    match = re.search(URL_RE, text)
    return match.group(0) if match else None


def clean_paper_name_from_question(text: str):
    lowered = text.lower()

    cut_positions = []

    for trigger in QUESTION_TRIGGERS:
        idx = lowered.find(trigger)
        if idx > 0:
            cut_positions.append(idx)

    if cut_positions:
        cut_at = min(cut_positions)
        possible_title = text[:cut_at].strip()
        possible_title = possible_title.strip(" ,.-:?")
        if len(possible_title.split()) >= 2:
            return possible_title

    return text.strip()


def looks_like_followup(text: str):
    lowered = text.lower()

    followup_terms = [
        "this paper",
        "above paper",
        "that paper",
        "the paper",
        "explain math",
        "explain equation",
        "summarize it",
        "explain it",
        "how does it work",
        "what is the input",
        "what is the output",
        "output size",
    ]

    return any(term in lowered for term in followup_terms)


def extract_paper_query(user_query: str, last_paper_query=None):
    url = extract_url(user_query)
    if url:
        return url

    arxiv_id = extract_arxiv_id(user_query)
    if arxiv_id:
        return arxiv_id

    if last_paper_query and looks_like_followup(user_query):
        return last_paper_query

    return clean_paper_name_from_question(user_query)