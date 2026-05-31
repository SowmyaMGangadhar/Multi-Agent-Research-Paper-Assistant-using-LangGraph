from langchain_core.output_parsers import PydanticOutputParser

from src.llm.ollama import get_llm
from src.agents.summarizer_agent import SummarizerAgent
from src.schemas.comparison_schema import ComparisonResult
from src.utils.parser_utils import clean_llm_json


class ComparisonAgent:

    def __init__(self):
        self.llm = get_llm()
        self.summarizer = SummarizerAgent()

        self.parser = PydanticOutputParser(
            pydantic_object=ComparisonResult
        )

    def run(self, paper_queries: list[str]) -> ComparisonResult:

        if len(paper_queries) < 2:
            raise ValueError("At least two papers are required for comparison.")

        paper_summaries = []

        for query in paper_queries:

            paper = self.summarizer.run(query)

            summary = paper["summary"]

            paper_summaries.append(
                f"""
TITLE:
{summary.title}

ABSTRACT:
{summary.abstract}

SUMMARY:
{summary.summary}
"""
            )

        papers_text = "\n\n".join(paper_summaries)

        prompt = f"""
            You are an expert AI research scientist.

            Compare the following research papers clearly and deeply.

            Papers:

            {papers_text}

            Your task:

            1. Compare the main goals of the papers.
            2. Compare their methods.
            3. Compare their architecture or algorithmic ideas.
            4. Compare their results.
            5. Explain similarities.
            6. Explain differences.
            7. Mention strengths and weaknesses.
            8. Give a final takeaway explaining when each paper is useful.

            Return ONLY valid JSON.

            {self.parser.get_format_instructions()}
            """

        response = self.llm.invoke(prompt)

        content = clean_llm_json(response.content)

        result = self.parser.parse(content)

        return result