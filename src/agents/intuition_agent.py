from langchain_core.output_parsers import PydanticOutputParser

from src.llm.ollama import get_llm

from src.schemas.response_schema import PaperSummary
from src.schemas.intuition_schema import IntuitionResponse
from src.utils.parser_utils import clean_llm_json



class IntuitionAgent:

    def __init__(self):

        self.llm = get_llm()

        self.parser = PydanticOutputParser(
            pydantic_object=IntuitionResponse
        )

    def run(
        self,
        paper_summary: PaperSummary
    ):

        prompt = f"""
            You are an expert teacher.

            Your task is to explain a research paper
            using intuition and real-world analogies.

            Paper Title:
            {paper_summary.title}

            Abstract:
            {paper_summary.abstract}

            Summary:
            {paper_summary.summary}

            Instructions:

            1. Explain the core idea in very simple language.

            2. Explain:
            - What problem the paper solves.
            - Why previous approaches struggled.
            - What new idea the authors introduced.
            - Why it works.

            3. Use real-world analogies.

            4. Explain as if teaching:

            - A college student
            - An ML beginner

            5. Avoid heavy mathematical notation.

            6. Keep explanations intuitive.

            7. Use bullet points.

            Return ONLY JSON.

            {self.parser.get_format_instructions()}
        """

        response = self.llm.invoke(prompt)

        content = clean_llm_json(
                response.content
            )

        result = self.parser.parse(
            content
        )

        return result