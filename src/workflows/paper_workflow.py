import time
from typing import TypedDict, Optional, List, Dict, Any

from langgraph.graph import StateGraph, END

from src.agents.router_agent import RouterAgent
from src.agents.summarizer_agent import SummarizerAgent
from src.agents.intuition_agent import IntuitionAgent
from src.agents.math_agent import MathAgent
from src.agents.comparison_agent import ComparisonAgent
from src.agents.response_agent import ResponseAgent
from langgraph.checkpoint.memory import MemorySaver
from src.agents.image_agent import ImageAgent


class PaperWorkflowState(TypedDict):
    query: str
    paper_queries: Optional[List[str]]

    route: Optional[str]

    paper: Optional[Dict[str, Any]]
    paper_query: Optional[str]
    summary: Optional[Any]
    equations: Optional[List[Dict[str, Any]]]
    tables: Optional[List[Dict[str, Any]]]
    sections: Optional[Dict[str, str]]

    intuition: Optional[Any]
    math_explanation: Optional[Any]
    comparison: Optional[Any]

    final_response: Optional[str]
    chat_history: Optional[List[Dict[str, str]]]
    user_question: Optional[str]
    chat_history: Optional[List[Dict[str, str]]]

    figures: Optional[List[Dict[str, Any]]]
    image_explanation: Optional[Any]
    timings: Optional[Dict[str, Any]]


router_agent = RouterAgent()
summarizer_agent = SummarizerAgent()
intuition_agent = IntuitionAgent()
math_agent = MathAgent()
comparison_agent = ComparisonAgent()
response_agent = ResponseAgent()
image_agent = ImageAgent()


def add_timing(state, key, elapsed):
    state["timings"] = state.get("timings") or {}
    state["timings"][key] = elapsed
    return state

def route_node(state):
    start = time.perf_counter()

    route = router_agent.run(state["query"])
    state["route"] = route

    elapsed = time.perf_counter() - start
    add_timing(state, "router_time", elapsed)

    return state

def image_node(state):
    start = time.perf_counter()

    state["image_explanation"] = image_agent.run(
        figures=state.get("figures") or [],
        user_question=state.get("user_question"),
        create_gif=False
    )

    elapsed = time.perf_counter() - start
    add_timing(state, "figure_explanation_time", elapsed)

    return state

def summarize_node(state):
    if state.get("summary") is not None:
        return state

    start = time.perf_counter()

    paper = summarizer_agent.run(state["query"])

    elapsed = time.perf_counter() - start
    add_timing(state, "summarization_time", elapsed)

    state["paper"] = paper
    state["summary"] = paper["summary"]
    state["equations"] = paper["equations"]
    state["tables"] = paper["tables"]
    state["sections"] = paper["sections"]
    state["figures"] = paper.get("figures", [])

    return state


def intuition_node(state):
    start = time.perf_counter()

    state["intuition"] = intuition_agent.run(
        state["summary"]
    )

    elapsed = time.perf_counter() - start
    add_timing(state, "intuition_time", elapsed)

    return state


def math_node(state):
    start = time.perf_counter()

    state["math_explanation"] = math_agent.run(
        state["summary"],
        state["equations"]
    )

    elapsed = time.perf_counter() - start
    add_timing(state, "math_explanation_time", elapsed)

    return state


def comparison_node(state):
    start = time.perf_counter()

    paper_queries = state.get("paper_queries")

    if not paper_queries:
        paper_queries = [state["query"]]

    state["comparison"] = comparison_agent.run(
        paper_queries
    )

    elapsed = time.perf_counter() - start
    add_timing(state, "comparison_time", elapsed)

    return state


def response_node(state):
    start = time.perf_counter()

    final = response_agent.run(
        summary=state.get("summary"),
        intuition=state.get("intuition"),
        math_explanation=state.get("math_explanation"),
        comparison=state.get("comparison"),
        chat_history=state.get("chat_history"),
        user_question=state.get("user_question")
    )

    state["final_response"] = final.answer

    elapsed = time.perf_counter() - start
    add_timing(state, "response_generation_time", elapsed)

    return state


def decide_route(state):
    route = state.get("route")

    if route == "unsupported":
        return "unsupported"

    if route == "comparison":
        return "comparison"

    if route == "math":
        return "math"

    if route == "intuition":
        return "intuition"

    if route == "image":
        return "image"

    return "summarizer"
def decide_after_summary(state):
    route = state.get("route")

    if route == "intuition":
        return "intuition"

    if route == "math":
        return "math"
    if route == "image":
        return "image"

    return "response"
def unsupported_node(state):
    state["final_response"] = (
        "I can only help with research paper questions. "
        "Please provide a valid arXiv ID, paper URL, or exact research paper title."
    )
    return state

def build_paper_workflow():
    graph = StateGraph(PaperWorkflowState)

    graph.add_node("router", route_node)
    graph.add_node("summarizer", summarize_node)
    graph.add_node("intuition", intuition_node)
    graph.add_node("math", math_node)
    graph.add_node("comparison", comparison_node)
    graph.add_node("response", response_node)
    graph.add_node("image", image_node)
    graph.add_node("unsupported", unsupported_node)

    graph.set_entry_point("router")

    graph.add_conditional_edges(
        "router",
        decide_route,
        {
            "summarizer": "summarizer",
            "intuition": "summarizer",
            "math": "summarizer",
            "image": "summarizer",
            "comparison": "comparison",
            "unsupported": "unsupported",
        }
    )

    # graph.add_edge("summarizer", "intuition")
    # graph.add_edge("intuition", "math")
    # graph.add_edge("math", "response")

    graph.add_conditional_edges(
    "summarizer",
    decide_after_summary,
    {
        "intuition": "intuition",
        "math": "math",
        "response": "response",
    }
)

    graph.add_edge("intuition", "response")
    graph.add_edge("math", "response")

    graph.add_edge("comparison", "response")

    graph.add_edge("response", END)
    graph.add_edge("unsupported", END)

    memory = MemorySaver()
    return graph.compile(checkpointer=memory)