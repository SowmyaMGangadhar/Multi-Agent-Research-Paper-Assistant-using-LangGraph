from src.llm.ollama import get_llm
from src.schemas.final_response_schema import FinalResponse


class ResponseAgent:

    def __init__(self):
        
        self.llm = get_llm()

    def run(
        self,
        summary=None,
        intuition=None,
        math_explanation=None,
        comparison=None,
        chat_history=None,
        user_question=None 
    ):
        if not summary and not comparison:
            return FinalResponse(
                answer="I could not find or load the paper context. Please provide a valid arXiv ID, paper URL, or exact paper title."
            )

        prompt = f"""
                You are an expert AI research paper assistant.

                You MUST answer the user's exact question using ONLY the available paper context and agent outputs.

                {user_question}

             
                {chat_history}

                {summary}

              
                {intuition}

               
                {math_explanation}

                {comparison}

              

                Before answering, internally check:

                1. Is there a valid paper summary or comparison?
                2. Is the user asking a follow-up about a previously loaded paper?
                3. Is the needed paper context available?

                If paper context is missing, answer ONLY:

                "I could not find or load the paper context. Please provide a valid arXiv ID, paper URL, or exact paper title."

                Do NOT answer from general knowledge.

                ==================================================
                ANSWERING RULES
                ==================================================

                1. Answer ONLY what the user asked.
                2. Do NOT generate a full paper report unless the user explicitly asks for a full explanation.
                3. Do NOT say "in few lines" unless user requested a short answer.
                4. If the user asks "in points", answer in clear bullet points.
                5. If the user asks "explain", give a complete explanation, not a tiny answer.
                6. If the user asks "briefly", "short", "few lines", or "few sentences", keep it short.
                7. If the user asks for math:
                - explain the relevant equation only
                - define variables
                - explain each term
                - explain why it matters
                - avoid unrelated equations
                8. If the user asks for architecture:
                - explain input
                - processing flow
                - key components
                - output
                - output shape if available
                9. If the user asks comparison:
                - compare only the requested papers/models
                - use clear differences
                10. Do not hallucinate paper details.
                11. If something is not in the paper context, say it is not available in the extracted context.
                12. Use markdown headings only when helpful.
                13. Prefer bullet points for clarity.
                14. Do not repeat the same idea.
                15. Do not include generic sections like Introduction, Methodology, Results unless the user asks for them.

                ==================================================
                FINAL ANSWER
                ==================================================

                Write the final answer now.
                """

        response = self.llm.invoke(prompt)

        content = response.content

        if isinstance(content, list):
            content = "\n".join(str(x) for x in content)

        return FinalResponse(answer=content.strip())