"""app.py - Streamlit chat over the coverage-policy RAG pipeline.

Run locally:  .venv\\Scripts\\streamlit run app.py
Uses rag.ask() with the main setup (section_ctx, insurer/drug filter on, k=8, no re-ranking).
The API key comes from the environment: .env locally (python-dotenv, loaded inside rag),
or Streamlit secrets when deployed. It is never displayed.
"""
import os

import streamlit as st

import rag

COLLECTION = "section_ctx"
K = rag.DEFAULT_K
EXAMPLES = [  # from eval/questions.jsonl, including one we can't answer
    "Does Cigna require a statin trial before approving Repatha?",
    "What tier is Prolia on Aetna's formulary, and what are its requirements?",
    "Cigna versus UnitedHealthcare: how long is the first Otezla approval for psoriatic arthritis?",
    "How often is Prolia given, and how?",
    "What is Humana's policy for Repatha?",
]
ABOUT = """\
This assistant answers questions about US insurer coverage policies for **Repatha**, \
**Prolia** and **Otezla** (Amgen drugs). Answers come only from the public policy, \
formulary and FDA label documents listed below, as of their version dates, and every \
claim cites its source.

It is a portfolio demo, **not coverage or medical advice**. Check the insurer's current \
policy before relying on an answer."""


def use_streamlit_secret():
    """When deployed, copy ANTHROPIC_API_KEY from Streamlit secrets into the environment."""
    try:
        if "ANTHROPIC_API_KEY" in st.secrets and not os.environ.get("ANTHROPIC_API_KEY"):
            os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:            # no secrets.toml (local runs): rag reads .env instead
        pass


@st.cache_resource(show_spinner="Loading the search index (first start only)...")
def warm_up():
    """Load the embedding model and Chroma client once per server, not on every rerun."""
    rag.retrieve("warm-up", COLLECTION, K)
    return True


def safe_markdown(text):
    """Markdown with dollar signs escaped, so amounts aren't rendered as LaTeX."""
    return text.replace("$", r"\$")


def show_sources(result):
    """Expander listing the retrieved sources, cited ones first, each with its chunk text."""
    sources, cited = result["sources"], result["cited"]
    texts = rag.raw_texts(COLLECTION)
    with st.expander(f"Sources ({len(cited)} cited of {len(sources)} retrieved)"):
        for r in sorted(sources, key=lambda r: (r["rank"] not in cited, r["rank"])):
            m = r["meta"]
            pages = f"p. {m['page_start']}" if m["page_start"] == m["page_end"] \
                else f"pp. {m['page_start']}-{m['page_end']}"
            status = "cited" if r["rank"] in cited else "retrieved, not cited"
            st.markdown(f"**[S{r['rank']}]** {rag.SOURCE_NAMES.get(m['source'], m['source'])} · "
                        f"{m['drug'].capitalize()} · {m['doc_type']} · {pages} · {m['version_date']}"
                        f"  \n{safe_markdown(m['section'] or '-')} · _{status}_")
            st.code(texts[r["chunk_id"]], language=None, wrap_lines=True)
        if result["invalid_citations"]:
            st.warning(f"The answer cites sources that weren't retrieved: "
                       f"{', '.join(result['invalid_citations'])}")


def answer(question):
    """Run the pipeline for one question -> chat message dict (assistant role)."""
    try:
        result = rag.ask(question, k=K, collection=COLLECTION, use_filter=True)
    except rag.AnswerError as e:
        return {"role": "assistant", "content": f"Sorry, I couldn't get an answer: {e}", "error": True}
    except Exception:
        return {"role": "assistant", "error": True,
                "content": "Sorry, something went wrong while answering. Please try again."}
    return {"role": "assistant", "content": result["answer"], "result": result}


def render(message):
    """Draw one chat message; assistant answers get their sources underneath."""
    with st.chat_message(message["role"]):
        if message.get("error"):
            st.error(message["content"])
            return
        st.markdown(safe_markdown(message["content"]))
        if "result" in message:
            show_sources(message["result"])


def sidebar():
    """About note, document list and example questions. Returns a clicked example, if any."""
    with st.sidebar:
        st.header("About")
        st.markdown(ABOUT)
        st.subheader("Documents in this knowledge base")
        st.markdown("\n".join(f"- {insurer} · {drug} · {doc_type} · {date}"
                              for insurer, drug, doc_type, date in rag.document_list()))
        st.subheader("Try an example")
        clicked = [q for i, q in enumerate(EXAMPLES) if st.button(q, key=f"example-{i}")]
        if st.button("Clear conversation", type="secondary"):
            st.session_state.messages = []
            st.rerun()
    return clicked[0] if clicked else None


def main():
    """Page layout: sidebar, chat history, then the new question if there is one."""
    st.set_page_config(page_title="Coverage policy assistant", page_icon="💊")
    use_streamlit_secret()
    st.title("Coverage policy assistant")
    st.caption("Repatha · Prolia · Otezla, from Aetna, Cigna and UnitedHealthcare policies "
               "and FDA labels. Each question is answered on its own.")
    st.session_state.setdefault("messages", [])

    example = sidebar()
    warm_up()
    for message in st.session_state.messages:
        render(message)

    question = st.chat_input("Ask about Repatha, Prolia or Otezla coverage...") or example
    if question:
        user_message = {"role": "user", "content": question}
        render(user_message)
        with st.spinner("Searching the policies and writing an answer..."):
            reply = answer(question)
        render(reply)
        st.session_state.messages += [user_message, reply]


main()
