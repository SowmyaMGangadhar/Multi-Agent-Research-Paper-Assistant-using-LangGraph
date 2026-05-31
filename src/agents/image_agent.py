from src.llm.ollama_vision import OllamaVisionClient
from src.schemas.image_schema import ImageAgentResponse, FigureExplanation


class ImageAgent:

    def __init__(self):
        self.vision_llm = OllamaVisionClient(
            model="qwen2.5vl:7b"
        )

    def run(
        self,
        figures,
        user_question=None,
        create_gif=False
    ):

        if not figures:
            return ImageAgentResponse(
                figures=[],
                gif_path=None
            )

        explanations = []

        for figure in figures[:5]:

            prompt = f"""
            Explain this research paper figure.

            User question:
            {user_question}

            Give:
            1. What the figure shows
            2. Main components
            3. Data/architecture flow
            4. Why it matters

            Keep it clear and concise.
            """

            explanation = self.vision_llm.ask_image(
                image_path=figure["path"],
                prompt=prompt
            )

            explanations.append(
                FigureExplanation(
                    page=figure["page"],
                    figure_index=figure["figure_index"],
                    image_path=figure["path"],
                    explanation=explanation
                )
            )

        gif_path = None

        explanations=explanations
            

        return ImageAgentResponse(
            figures=explanations,
            
        )