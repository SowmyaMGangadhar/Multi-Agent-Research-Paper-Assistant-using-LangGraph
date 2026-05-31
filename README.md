# Multi-Agent-Research-Paper-Assistant-using-LangGraph

A multi-agent AI system that helps users understand research papers from arXiv, paper URLs, or paper titles. The system can summarize papers, explain math equations, provide intuitive explanations, compare multiple papers, and explain figures/architecture diagrams using local LLMs.

## Features

- Search and load research papers using arXiv ID, paper title, or URL
- Extract paper sections, tables, equations, and figures from PDFs
- Multi-agent workflow using LangGraph
- Router agent to select the right task-specific agent
- Summarizer agent for structured paper summaries
- Math agent for equation-level explanations
- Intuition agent for simple conceptual explanations
- Comparison agent for comparing multiple papers/models
- Image agent for explaining paper figures and architecture diagrams
- Stateful chat interface for follow-up questions
- Streamlit UI and FastAPI backend
- Local model support using Ollama

## Architecture

![LangGraph Workflow](screenshots/langgraph_workflow.png)
![alt text](image-1.png)

The system uses LangGraph to orchestrate multiple agents:

- Router Agent
- Summarizer Agent
- Math Agent
- Intuition Agent
- Comparison Agent
- Image Agent
- Response Agent

## Screenshots

### Streamlit Chat Interface

![Streamlit UI](screenshots/streamlit_ui.png)
![alt text](screencapture-localhost-8501-2026-05-31-22_10_44.webp)

### Figure Explanation

![Figure Explanation](screenshots/figure_explanation.png)
![alt text](image-2.png)

### Evaluation Results

![Evaluation Results](screenshots/evaluation_results.png)
![alt text](image.png)

## Evaluation

The system was evaluated on research-paper tasks including summarization, math explanation, intuition explanation, comparison, and unsupported-query handling.

| Metric | Score |
|---|---:|
| Route Accuracy | 88.9% |
| Answer Relevance | 87.2% |
| Faithfulness | 92.8% |
| Completeness | 86.1% |
| Conciseness Control | 97.2% |
| Final Quality Score | 88.9% |

## Tech Stack

- Python
- LangGraph
- LangChain
- FastAPI
- Streamlit
- Pydantic
- PyMuPDF
- Ollama
- Qwen / Qwen2.5-VL
- Local LLMs
- Multimodal AI

## Project Structure

```text
research-paper-agent/
├── src/
│   ├── agents/
│   ├── workflows/
│   ├── tools/
│   ├── schemas/
│   ├── llm/
│   └── evaluation/
├── streamlit_app.py
├── requirements.txt
├── README.md
└── screenshots/