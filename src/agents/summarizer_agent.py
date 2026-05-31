import json
import re

from src.llm.ollama import get_llm
from src.schemas.response_schema import PaperSummary
from src.tools.paper_laoder import PaperLoader


class SummarizerAgent:

    def __init__(self):
        self.llm = get_llm()

    def _clean_json_response(self, content):

        if isinstance(content, list):
            content = "\n".join(str(x) for x in content)

        content = content.strip()

        content = re.sub(r"^```json", "", content, flags=re.IGNORECASE)
        content = re.sub(r"^```", "", content)
        content = re.sub(r"```$", "", content)

        content = content.strip()

        start = content.find("{")
        end = content.rfind("}")

        if start == -1 or end == -1:
            raise ValueError(f"Could not find JSON in LLM response: {content}")

        return content[start:end + 1]

    def run(self, query):

        paper_data = PaperLoader.load(query)

        title = paper_data["title"]

        # sections_text = "\n\n".join(
        #     f"{section_title}\n{section_content}"
        #     for section_title, section_content in paper_data["sections"].items()
        # )
        sections_text = self._compress_sections(
                paper_data["sections"],
                max_chars=7000
            )

        equations_text = "\n".join(
            eq["text"]
            for eq in paper_data["equations"][:10]
        )

        prompt = f"""
                You are a research paper summarizer.

                Return ONLY valid JSON.
                Do not use markdown.
                Do not use code fences.
                Do not call tools.
                Do not output function syntax.
                Do not include text outside JSON.

                Required JSON format:

                {{
                "title": "paper title as a string",
                "abstract": "paper abstract as a string",
                "summary": "summary as one single string. If using points, put bullet points inside this string using newline characters."
                }}

                Important:
                - title MUST be a string.
                - abstract MUST be a string.
                - summary MUST be a string.
                - Do NOT return summary as a list.
                - Do NOT return arrays.

                Rules:
                - The summary must answer the user's paper request.
                - Keep the summary clean and educational.
                - Use concise points inside the summary string.
                - Do not invent details.
                - Use only the provided paper sections.
                - If important math appears, briefly mention it in simple words.

                Paper Title:
                {title}

                Paper Sections:
                {sections_text[:7000]}

                Important Equations:
                {equations_text[:1000]}
                """

        response = self.llm.invoke(prompt)

        content = self._clean_json_response(response.content)

        data = json.loads(content)

        data = self._normalize_paper_summary_data(data)

        result = PaperSummary(**data)

        return {
            "summary": result,
            "equations": paper_data["equations"],
            "tables": paper_data["tables"],
            "sections": paper_data["sections"],
            "figures": paper_data.get("figures", [])
        }
    def _compress_sections(self, sections, max_chars=7000):
        priority_keywords = [
            "abstract",
            "introduction",
            "method",
            "approach",
            "architecture",
            "model",
            "experiment",
            "result",
            "conclusion"
        ]

        selected = []

        for title, content in sections.items():
            title_lower = title.lower()

            if any(k in title_lower for k in priority_keywords):
                selected.append(
                    f"{title}\n{content[:1200]}"
                )

        if not selected:
            selected = [
                f"{title}\n{content[:1000]}"
                for title, content in list(sections.items())[:5]
            ]

        text = "\n\n".join(selected)

        return text[:max_chars]
    def _normalize_paper_summary_data(self, data):
        title = data.get("title", "")
        abstract = data.get("abstract", "")
        summary = data.get("summary", "")

        if isinstance(title, list):
            title = " ".join(str(x) for x in title)

        if isinstance(abstract, list):
            abstract = "\n".join(str(x) for x in abstract)

        if isinstance(summary, list):
            summary = "\n".join(f"- {str(x)}" for x in summary)

        if not isinstance(summary, str):
            summary = str(summary)

        if not isinstance(abstract, str):
            abstract = str(abstract)

        if not isinstance(title, str):
            title = str(title)

        return {
            "title": title.strip(),
            "abstract": abstract.strip(),
            "summary": summary.strip(),
        }