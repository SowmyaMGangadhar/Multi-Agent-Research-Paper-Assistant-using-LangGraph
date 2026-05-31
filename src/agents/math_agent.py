import json
import re

from src.llm.ollama import get_llm

from src.schemas.response_schema import PaperSummary
from src.schemas.math_schema import MathResponse, EquationExplanation
from src.utils.parser_utils import clean_llm_json


class MathAgent:

    def __init__(self):
        self.llm = get_llm()

    def _extract_json(self, content):
        if isinstance(content, list):
            content = "\n".join(str(x) for x in content)

        content = clean_llm_json(content)

        content = content.strip()

        start = content.find("{")
        end = content.rfind("}")

        if start == -1 or end == -1:
            return None

        return content[start:end + 1]

    def _safe_parse(self, content):
        json_text = self._extract_json(content)

        if not json_text:
            return MathResponse(equations=[])

        if '"$defs"' in json_text or '"properties"' in json_text:
            return MathResponse(equations=[])

        try:
            data = json.loads(json_text)
        except Exception:
            return MathResponse(equations=[])

        if "equations" not in data:
            return MathResponse(equations=[])

        parsed_equations = []

        for item in data.get("equations", []):

            if not isinstance(item, dict):
                continue

            parsed_equations.append(
                EquationExplanation(
                    equation=item.get("equation", ""),
                    variables=item.get("variables", ""),
                    explanation=item.get("explanation", ""),
                    intuition=item.get(
                        "intuition",
                        "No separate intuition provided."
                    )
                )
            )

        return MathResponse(equations=parsed_equations)

    def run(
        self,
        paper_summary: PaperSummary,
        equations: list
    ) -> MathResponse:

        if not equations:
            return MathResponse(equations=[])

        equation_text = "\n\n".join(
            eq.get("text", "")
            for eq in equations[:5]
            if eq.get("text")
        )

        if not equation_text.strip():
            return MathResponse(equations=[])

        prompt = f"""
                You are a mathematics explainer for research papers.

                Paper Title:
                {paper_summary.title}

                Paper Summary:
                {paper_summary.summary[:2000]}

                Extracted Equations:
                {equation_text[:1500]}

                Your task:
                Explain only the important equations from the extracted equations.

                For each equation:
                - rewrite the equation clearly
                - explain variables
                - explain step-by-step meaning
                - explain intuition simply

                Return ONLY valid JSON in this exact format:

                {{
                "equations": [
                    {{
                    "equation": "write the equation here",
                    "variables": "explain variables here",
                    "explanation": "step-by-step explanation here",
                    "intuition": "simple intuition here"
                    }}
                ]
                }}

                Important rules:
                - Do not return the JSON schema.
                - Do not return $defs.
                - Do not return properties.
                - Do not return required.
                - Do not use markdown code fences.
                - Do not include text outside JSON.
                - If equations are corrupted or unclear, return:
                {{
                "equations": []
                }}
                """

        response = self.llm.invoke(prompt)

        return self._safe_parse(response.content)