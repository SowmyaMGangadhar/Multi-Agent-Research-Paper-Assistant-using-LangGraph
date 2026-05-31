import os
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from src.workflows.paper_workflow import build_paper_workflow
from src.utils.query_utils import extract_paper_query
from src.agents.image_agent import ImageAgent
# from src.agents.gif_agent import GifAgent


app = FastAPI(
    title="Research Paper Multi-Agent AI",
    version="1.0.0"
)

workflow = build_paper_workflow()
image_agent = ImageAgent()
# gif_agent = GifAgent()

CHAT_STORE = {}
SESSION_PAPERS = {}
SESSION_CONTEXT = {}


class ChatRequest(BaseModel):
    session_id: str
    query: str
    paper_queries: Optional[List[str]] = None


class FigureExplainRequest(BaseModel):
    session_id: str
    figure_index: int
    question: str = "Explain this figure step by step"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(request: ChatRequest):
    try:
        history = CHAT_STORE.get(request.session_id, [])

        last_paper_query = SESSION_PAPERS.get(request.session_id)

        paper_query = extract_paper_query(
            request.query,
            last_paper_query
        )

        lower_query = request.query.lower()

        if any(word in lower_query for word in ["gif", "animation", "animate"]):

            context = SESSION_CONTEXT.get(request.session_id, {})

            # result = gif_agent.run(
            #     user_question=request.query,
            #     summary=context.get("summary"),
            #     math_explanation=context.get("math_explanation"),
            #     intuition=context.get("intuition")
            # )

            answer = result["answer"]

            if result.get("gif_path"):
                answer += f"\n\nGIF path: `{result['gif_path']}`"

            history.append(
                {
                    "role": "user",
                    "content": request.query
                }
            )

            history.append(
                {
                    "role": "assistant",
                    "content": answer
                }
            )

            CHAT_STORE[request.session_id] = history[-10:]

            return {
                "session_id": request.session_id,
                "paper_query": last_paper_query,
                "answer": answer,
                "history": CHAT_STORE[request.session_id],
                "figures": [],
                # "gif_path": result.get("gif_path")
            }
        

        result = workflow.invoke(
            {
                "query": paper_query,
                "user_question": request.query,
                "paper_queries": request.paper_queries,
                "chat_history": history,

                "route": None,
                "paper": None,
                "summary": None,
                "equations": None,
                "tables": None,
                "sections": None,
                "figures": None,
                "image_explanation": None,
                "intuition": None,
                "math_explanation": None,
                "comparison": None,
                "final_response": None,
            },
            config={
                "configurable": {
                    "thread_id": request.session_id
                }
            }
        )

        answer = result.get("final_response")

        if not answer:
            answer = "I could not generate a response."

        SESSION_PAPERS[request.session_id] = paper_query

        SESSION_CONTEXT[request.session_id] = {
            "paper_query": paper_query,
            "summary": result.get("summary"),
            "equations": result.get("equations"),
            "tables": result.get("tables"),
            "sections": result.get("sections"),
            "figures": result.get("figures") or [],
        }

        history.append(
            {
                "role": "user",
                "content": request.query
            }
        )

        history.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        CHAT_STORE[request.session_id] = history[-10:]

        return {
            "session_id": request.session_id,
            "paper_query": paper_query,
            "answer": answer,
            "history": CHAT_STORE[request.session_id],
            "figures": result.get("figures") or []
        }
    except ValueError as e:
        return {
            "session_id": request.session_id,
            "paper_query": None,
            "answer": str(e),
            "history": CHAT_STORE.get(request.session_id, []),
            "figures": []
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/figures/{session_id}")
def get_figures(session_id: str):
    context = SESSION_CONTEXT.get(session_id)

    if not context:
        return {
            "figures": []
        }

    return {
        "paper_query": context.get("paper_query"),
        "figures": context.get("figures", [])
    }


@app.post("/figures/explain")
def explain_selected_figure(request: FigureExplainRequest):
    try:
        context = SESSION_CONTEXT.get(request.session_id)

        if not context:
            raise ValueError(
                "No paper context found. Please load a paper first."
            )

        figures = context.get("figures", [])

        if not figures:
            raise ValueError(
                "No figures found for the loaded paper."
            )

        if request.figure_index < 0 or request.figure_index >= len(figures):
            raise ValueError(
                "Invalid figure index."
            )

        selected_figure = figures[request.figure_index]

        result = image_agent.run(
            figures=[selected_figure],
            user_question=request.question,
            create_gif=False
        )

        if not result.figures:
            answer = "Could not explain the selected figure."
            image_path = selected_figure.get("path")
        else:
            answer = result.figures[0].explanation
            image_path = result.figures[0].image_path

        history = CHAT_STORE.get(request.session_id, [])

        history.append(
            {
                "role": "user",
                "content": f"Explain selected figure: {request.question}"
            }
        )

        history.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        CHAT_STORE[request.session_id] = history[-10:]

        return {
            "answer": answer,
            "image_path": image_path,
            "figure": selected_figure
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.post("/image/explain")
async def explain_uploaded_image(
    image: UploadFile = File(...),
    question: str = Form("Explain this architecture figure step by step")
):
    try:
        upload_dir = "data/outputs/uploaded_images"

        Path(upload_dir).mkdir(
            parents=True,
            exist_ok=True
        )

        image_path = os.path.join(
            upload_dir,
            image.filename
        )

        with open(image_path, "wb") as f:
            f.write(await image.read())

        figures = [
            {
                "page": 0,
                "figure_index": 1,
                "figure_name": image.filename,
                "path": image_path,
                "extension": image.filename.split(".")[-1]
            }
        ]

        result = image_agent.run(
            figures=figures,
            user_question=question,
            create_gif=False
        )

        explanation = (
            result.figures[0].explanation
            if result.figures
            else "Could not explain image."
        )

        return {
            "image_path": image_path,
            "answer": explanation
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )