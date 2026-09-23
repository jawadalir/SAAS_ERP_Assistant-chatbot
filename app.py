"""
app.py
------
Streamlit UI for the FAQ RAG chatbot.

Run with:
    streamlit run app.py
"""

import streamlit as st
from rag_engine import RAGEngine

st.set_page_config(page_title="FAQ Assistant", page_icon="💬", layout="centered")

# ---------------------------------------------------------------------------
# Light custom styling for a cleaner, more modern look
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .main .block-container { padding-top: 2rem; max-width: 780px; }
    [data-testid="stChatMessage"] {
        border-radius: 14px;
        padding: 0.4rem 0.2rem;
    }
    .app-header {
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .app-subtitle {
        text-align: center;
        color: #8a8f98;
        margin-bottom: 1.5rem;
        font-size: 0.95rem;
    }
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-left: 6px;
    }
    .badge-general { background: #fff3cd; color: #7a5b00; }
    .badge-strict { background: #d4edda; color: #155724; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<h1 class='app-header'>💬 FAQ Assistant</h1>", unsafe_allow_html=True)
st.markdown(
    "<div class='app-subtitle'>Ask a question and I'll answer using our FAQ documents.</div>",
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner="Loading knowledge base...")
def load_engine():
    return RAGEngine()


# Try to load the engine, with a friendly error if setup isn't done yet.
try:
    engine = load_engine()
except FileNotFoundError as e:
    st.error(str(e))
    st.info("Run `python ingest.py` in your terminal first, then refresh this page.")
    st.stop()
except EnvironmentError as e:
    st.error(str(e))
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Response settings")

    length_choice = st.radio(
        "Response length",
        options=["brief", "medium", "detailed"],
        index=1,
        format_func=lambda x: {"brief": "Brief", "medium": "Medium", "detailed": "Detailed"}[x],
        help="Controls how long the assistant's answers are.",
    )

    mode_choice = st.radio(
        "Answer source",
        options=["general", "strict"],
        index=0,
        format_func=lambda x: {
            "general": "Data + General knowledge",
            "strict": "FAQ data only",
        }[x],
        help=(
            "Data + General knowledge: uses FAQ docs first, falls back to the "
            "model's general knowledge (clearly labeled) if not covered. "
            "FAQ data only: never answers outside the FAQ documents."
        ),
    )

    st.markdown("---")
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            with st.expander("📎 Sources"):
                for s in msg["sources"]:
                    st.markdown(f"**{s['source']}**")
                    st.caption(s["snippet"] + "...")

# Chat input
if question := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer, sources = engine.ask(question, length=length_choice, mode=mode_choice)
            st.markdown(answer)
            if sources:
                with st.expander("📎 Sources"):
                    for s in sources:
                        st.markdown(f"**{s['source']}**")
                        st.caption(s["snippet"] + "...")

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": sources}
    )