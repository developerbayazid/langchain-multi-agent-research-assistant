
import queue
import threading
import time

import streamlit as st

from src.pipelines.pipelines import run_research_pipeline


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Research Assistant",
    page_icon="🔎",
    layout="wide",
)

# Claude-inspired, clean research workspace
st.markdown(
    """
    <style>
    .stApp {
        background-color: #FAF9F6;
    }

    [data-testid="stSidebar"] {
        background-color: #F1EFEA;
    }

    .app-heading {
        font-size: 2rem;
        font-weight: 650;
        letter-spacing: -0.8px;
        color: #282722;
    }

    .app-subheading {
        color: #77746C;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }

    .processing-text {
        color: #77746C;
        font-size: 0.9rem;
    }

    div[data-testid="stChatMessage"] {
        border-radius: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Session state
# --------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []


# --------------------------------------------------
# Header
# --------------------------------------------------

with st.sidebar:
    st.title("🔎 Research Assistant")
    st.caption("Powered by LangChain")

    st.divider()

    st.markdown("### Research workflow")
    st.markdown(
        """
        1. 🔍 Search reliable sources
        2. 📚 Read relevant webpages
        3. ✍️ Write the research report
        4. 🧐 Critique the report
        """
    )

    st.divider()

    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


st.markdown(
    '<div class="app-heading">Research Assistant</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="app-subheading">'
    'Explore a topic, gather evidence, and generate a structured report.'
    '</div>',
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Display previous conversation
# --------------------------------------------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["content"])
        else:
            st.markdown("### Research report")
            st.markdown(message["report"])

            with st.expander("View critic feedback"):
                st.markdown(message["feedback"])


# --------------------------------------------------
# Background worker
# --------------------------------------------------

def research_worker(topic, event_queue, result_holder):
    """Run the pipeline outside the Streamlit UI thread."""

    def progress_callback(stage, message):
        event_queue.put(("stage", stage, message))

    try:
        result = run_research_pipeline(
            topic,
            progress_callback=progress_callback,
        )

        result_holder["result"] = result
        event_queue.put(("done", None, None))

    except Exception as exc:
        result_holder["error"] = str(exc)
        event_queue.put(("error", None, None))


# --------------------------------------------------
# Chat input
# --------------------------------------------------

prompt = st.chat_input(
    "What would you like to research?",
)

if prompt:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):

        status_box = st.status(
            "Preparing your research...",
            expanded=True,
        )

        timer_placeholder = st.empty()

        event_queue = queue.Queue()
        result_holder = {}

        worker = threading.Thread(
            target=research_worker,
            args=(prompt, event_queue, result_holder),
            daemon=True,
        )

        start_time = time.monotonic()
        worker.start()

        stage_names = {
            "search": "🔍 Searching the web",
            "reader": "📚 Reading webpages",
            "writer": "✍️ Writing the report",
            "critic": "🧐 Reviewing the report",
        }

        completed = False
        failed = False

        while not completed:
            try:
                event_type, stage, message = event_queue.get(
                    timeout=0.2
                )

                if event_type == "stage":
                    stage_title = stage_names.get(
                        stage,
                        "Processing",
                    )

                    status_box.write(
                        f"**{stage_title}**\n\n{message}"
                    )

                    status_box.update(
                        label=stage_title,
                        state="running",
                        expanded=True,
                    )

                elif event_type == "done":
                    completed = True

                elif event_type == "error":
                    failed = True
                    completed = True

            except queue.Empty:
                pass

            elapsed = int(time.monotonic() - start_time)

            if not completed:
                timer_placeholder.markdown(
                    f'<div class="processing-text">'
                    f'⏳ Processing · {elapsed}s'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        worker.join()

        elapsed = int(time.monotonic() - start_time)

        if failed or "error" in result_holder:
            status_box.update(
                label="Research failed",
                state="error",
                expanded=True,
            )

            st.error(
                "The pipeline encountered an error: "
                + result_holder.get(
                    "error",
                    "Unknown error",
                )
            )

        else:
            result = result_holder["result"]

            status_box.update(
                label=f"Research completed in {elapsed}s",
                state="complete",
                expanded=False,
            )

            timer_placeholder.caption(
                f"Completed in {elapsed} seconds"
            )

            st.markdown("### Research report")
            st.markdown(result["report"])

            with st.expander("View critic feedback"):
                st.markdown(result["feedback"])

            with st.expander("View search results"):
                st.markdown(
                    result.get(
                        "search_results",
                        "No search results available.",
                    )
                )

            with st.expander("View scraped content"):
                st.markdown(
                    result.get(
                        "scraped_content",
                        "No scraped content available.",
                    )
                )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "report": result["report"],
                    "feedback": result["feedback"],
                }
            )
