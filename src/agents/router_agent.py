from src.llm.ollama import get_llm


class RouterAgent:

    def __init__(self):
        self.llm = get_llm()

    def run(self, query):
        q = query.lower()

        unsupported_terms = [
            "weather",
            "stock price",
            "movie ticket",
            "restaurant",
            "recipe",
            "cricket score",
            "news today",
        ]

        if any(term in q for term in unsupported_terms):
            return "unsupported"

        if any(term in q for term in ["compare", "difference between", "versus", " vs "]):
            return "comparison"

        if any(term in q for term in ["figure", "diagram", "image", "architecture figure", "visualization"]):
            return "image"

        if any(term in q for term in ["equation", "loss", "objective", "math", "formula"]):
            return "math"

        if any(term in q for term in ["intuition", "intuitively", "simple terms", "analogy"]):
            return "intuition"

        if any(term in q for term in ["summarize", "summary", "explain", "input", "output", "architecture", "how does"]):
            return "summarizer"

        prompt = f"""
            You are a router for a research-paper assistant.

            Choose exactly one route:

            summarizer
            math
            intuition
            comparison
            image
            unsupported

            User query:
            {query}

            Rules:
            - research paper summary/explanation/input/output/architecture -> summarizer
            - equation/loss/objective/formula/math -> math
            - intuitive/simple/analogy -> intuition
            - compare/vs/difference -> comparison
            - figure/image/diagram/architecture figure -> image
            - unrelated to research papers -> unsupported

            Return only the route name.
            """

        response = self.llm.invoke(prompt)
        route = response.content.strip().lower()

        valid_routes = {
            "summarizer",
            "math",
            "intuition",
            "comparison",
            "image",
            "unsupported",
        }

        if route not in valid_routes:
            return "unsupported"

        return route