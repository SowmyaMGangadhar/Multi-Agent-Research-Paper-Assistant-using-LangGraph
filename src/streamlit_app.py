import uuid
import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="Research Paper AI Agent",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Multi-Agent Research Paper Assistant")
st.caption(
    "Ask about arXiv papers, paper URLs, summaries, math, intuition, comparisons, or figures."
)


if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "figures" not in st.session_state:
    st.session_state.figures = []

if "paper_query" not in st.session_state:
    st.session_state.paper_query = None


with st.sidebar:
    st.header("Session")

    st.write("Session ID:")
    st.code(st.session_state.session_id)

    if st.session_state.paper_query:
        st.write("Current paper:")
        st.code(st.session_state.paper_query)

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.session_state.figures = []
        st.session_state.paper_query = None
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

    st.markdown("---")

    st.markdown(
        """
        **Example questions**

        - `1706.03762 summarize this paper`
        - `1506.02640 explain YOLO input and output`
        - `Attention Is All You Need summarize in points`
        - `Explain the math in this paper`
        - `Explain the architecture figure`
        - `Compare BERT and GPT`
        """
    )


left_col, right_col = st.columns([2, 1])


with left_col:
    st.subheader("💬 Chat")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_query = st.chat_input(
        "Ask about a paper, arXiv ID, URL, math, intuition, comparison, or figures..."
    )

    if user_query:
        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_query
            }
        )

        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            with st.spinner("Running multi-agent workflow..."):
                try:
                    response = requests.post(
                        f"{API_URL}/chat",
                        json={
                            "session_id": st.session_state.session_id,
                            "query": user_query,
                            "paper_queries": None
                        },
                        timeout=600
                    )

                    if response.status_code == 200:
                        data = response.json()

                        answer = data.get(
                            "answer",
                            "No answer returned."
                        )


                        st.markdown(answer)

                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": answer
                            }
                        )

                        st.session_state.figures = data.get(
                            "figures",
                            []
                        )

                        st.session_state.paper_query = data.get(
                            "paper_query"
                        )

                    else:
                        error = response.json().get(
                            "detail",
                            "Something went wrong."
                        )
                        st.error(error)

                except requests.exceptions.ConnectionError:
                    st.error(
                        "FastAPI backend is not running. Start it with: uvicorn src.app:app --reload"
                    )

                except Exception as e:
                    st.error(str(e))


with right_col:
    st.subheader("🖼️ Paper Figures")

    if not st.session_state.figures:
        st.info(
            "Load a paper first. Extracted figures will appear here."
        )
    else:
        figure_labels = []

        for i, fig in enumerate(st.session_state.figures):
            label = fig.get(
                "figure_name",
                f"Figure {i + 1}"
            )

            page = fig.get("page", "unknown")

            figure_labels.append(
                f"{i}: {label} | page {page}"
            )

        selected_label = st.selectbox(
            "Select a figure",
            figure_labels
        )

        selected_index = int(
            selected_label.split(":")[0]
        )

        selected_figure = st.session_state.figures[
            selected_index
        ]

        image_path = selected_figure.get("path")

        if image_path:
            st.image(
                image_path,
                caption=selected_figure.get(
                    "figure_name",
                    "Selected Figure"
                ),
                use_container_width=True
            )

        figure_question = st.text_area(
            "Question about selected figure",
            value="Explain this figure step by step. If it is an architecture diagram, explain the flow."
        )

        if st.button("Explain Selected Figure"):
            with st.spinner(
                "Image agent is analyzing selected figure..."
            ):
                try:
                    response = requests.post(
                        f"{API_URL}/figures/explain",
                        json={
                            "session_id": st.session_state.session_id,
                            "figure_index": selected_index,
                            "question": figure_question
                        },
                        timeout=300
                    )

                    if response.status_code == 200:
                        data = response.json()

                        answer = data.get(
                            "answer",
                            "No explanation returned."
                        )

                        st.markdown("### Figure Explanation")
                        st.markdown(answer)

                        st.session_state.messages.append(
                            {
                                "role": "user",
                                "content": f"[Figure {selected_index}] {figure_question}"
                            }
                        )

                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": answer
                            }
                        )

                    else:
                        st.error(
                            response.json().get(
                                "detail",
                                "Figure explanation failed."
                            )
                        )

                except Exception as e:
                    st.error(str(e))

    st.markdown("---")

    st.subheader("📤 Upload Image")

    uploaded_image = st.file_uploader(
        "Upload a paper figure or architecture image",
        type=["png", "jpg", "jpeg", "webp"]
    )

    uploaded_question = st.text_input(
        "Question about uploaded image",
        value="Explain this architecture diagram step by step"
    )

    if uploaded_image is not None:
        st.image(
            uploaded_image,
            caption="Uploaded image",
            use_container_width=True
        )

        if st.button("Explain Uploaded Image"):
            with st.spinner(
                "Image agent is analyzing uploaded image..."
            ):
                try:
                    files = {
                        "image": (
                            uploaded_image.name,
                            uploaded_image.getvalue(),
                            uploaded_image.type
                        )
                    }

                    data = {
                        "question": uploaded_question
                    }

                    response = requests.post(
                        f"{API_URL}/image/explain",
                        files=files,
                        data=data,
                        timeout=300
                    )

                    if response.status_code == 200:
                        result = response.json()

                        answer = result.get(
                            "answer",
                            "No explanation returned."
                        )

                        st.markdown("### Uploaded Image Explanation")
                        st.markdown(answer)

                        st.session_state.messages.append(
                            {
                                "role": "user",
                                "content": f"[Uploaded image] {uploaded_question}"
                            }
                        )

                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": answer
                            }
                        )

                    else:
                        st.error(
                            response.json().get(
                                "detail",
                                "Image explanation failed."
                            )
                        )

                except Exception as e:
                    st.error(str(e))