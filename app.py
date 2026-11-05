"""app.py - Streamlit chat over the coverage-policy RAG pipeline.

Run locally:  .venv\\Scripts\\streamlit run app.py   (needs APP_PASSWORD in .env)
Uses rag.ask() with the main setup (section_ctx, insurer/drug filter on, k=8, no re-ranking).
Settings come from the environment: .env locally (python-dotenv), Space secrets when
deployed (environment variables), or Streamlit secrets. Keys and passwords are never shown.
On a fresh server without chroma_db/ and data/chunks.jsonl, the app downloads them from the
private Hugging Face dataset DATA_REPO using HF_TOKEN.
"""
import hmac
import json
import os
import tempfile
import threading
import time
from datetime import date
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

rag = None   # imported in main() after the password gate: it loads torch (~30 s on a cold start)

COLLECTION = "section_ctx"
SETTINGS = ["ANTHROPIC_API_KEY", "APP_PASSWORD", "HF_TOKEN"]
DATA_REPO = os.environ.get("DATA_REPO", "ree57/payer-policy-copilot-data")   # private HF dataset
DATA_FILES = [Path("chroma_db/chroma.sqlite3"), Path("data/chunks.jsonl")]
MAX_PASSWORD_ATTEMPTS = 5
WRONG_PASSWORD_DELAY = 2                          # seconds, to slow down guessing
MAX_PER_SESSION = int(os.environ.get("MAX_QUESTIONS_PER_SESSION", 20))
MAX_PER_DAY = int(os.environ.get("MAX_QUESTIONS_PER_DAY", 150))
# The daily counter lives in the container's temp folder, so it resets whenever the
# container restarts (including when a free Space goes to sleep). Fine for a demo.
USAGE_FILE = Path(tempfile.gettempdir()) / "payer-copilot-usage.json"
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


def load_settings():
    """Fill the environment from .env (local) and Streamlit secrets, without overriding it."""
    load_dotenv(encoding="utf-8-sig")
    for name in SETTINGS:
        try:
            if name in st.secrets and not os.environ.get(name):
                os.environ[name] = st.secrets[name]
        except Exception:        # no secrets.toml: the environment / .env is used instead
            pass


def password_gate():
    """Stop the page until the right password is entered; nothing else renders before that."""
    expected = os.environ.get("APP_PASSWORD")
    if not expected:
        st.error("This app isn't configured: APP_PASSWORD is not set, so it won't start unprotected.")
        st.stop()
    if st.session_state.get("unlocked"):
        return
    st.title("Coverage policy assistant")
    failures = st.session_state.get("password_failures", 0)
    if failures >= MAX_PASSWORD_ATTEMPTS:
        st.error("Too many wrong passwords. This session is locked.")
        st.stop()
    with st.form("login"):
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Unlock")
    if submitted:
        if hmac.compare_digest(password.encode(), expected.encode()):
            st.session_state.unlocked = True
            st.rerun()
        time.sleep(WRONG_PASSWORD_DELAY)
        st.session_state.password_failures = failures = failures + 1
        if failures >= MAX_PASSWORD_ATTEMPTS:
            st.rerun()              # redraw as the locked screen, without the form
        st.error(f"Wrong password. {MAX_PASSWORD_ATTEMPTS - failures} attempt(s) left.")
    st.stop()


@st.cache_resource(show_spinner="Downloading the search index (first start only)...")
def ensure_data():
    """Download chroma_db/ and data/chunks.jsonl from the private dataset if they're missing.

    Locally the files exist, so nothing is downloaded. Failures raise (and aren't cached),
    so the next page load retries.
    """
    if all(p.exists() for p in DATA_FILES):
        return True
    if not DATA_REPO or not os.environ.get("HF_TOKEN"):
        raise RuntimeError("The search data is missing, and DATA_REPO or HF_TOKEN isn't set.")
    from huggingface_hub import snapshot_download
    try:
        snapshot_download(DATA_REPO, repo_type="dataset", token=os.environ["HF_TOKEN"], local_dir=".",
                          allow_patterns=["chroma_db/*", "data/chunks.jsonl"])  # not the dataset's README
    except Exception as e:       # report the error type only: messages could include URLs
        raise RuntimeError(f"Could not download the search data ({type(e).__name__}).") from None
    return True


@st.cache_resource
def usage_lock():
    """One lock shared by all sessions, so two questions can't update the counter at once."""
    return threading.Lock()


def take_daily_slot():
    """Count one question against the server-wide daily cap; False if the cap is reached."""
    today = date.today().isoformat()
    with usage_lock():
        try:
            usage = json.loads(USAGE_FILE.read_text())
        except (FileNotFoundError, ValueError):
            usage = {}
        count = usage.get("count", 0) if usage.get("date") == today else 0
        if count >= MAX_PER_DAY:
            return False
        USAGE_FILE.write_text(json.dumps({"date": today, "count": count + 1}))
        return True


@st.cache_resource(show_spinner="Loading the search index (first start only)...")
def warm_up():
    """Load the embedding model and Chroma client once per server, not on every rerun."""
    rag.retrieve("warm-up", COLLECTION, rag.DEFAULT_K)
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
        result = rag.ask(question, k=rag.DEFAULT_K, collection=COLLECTION, use_filter=True)
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
        if message.get("notice"):
            st.info(message["content"])
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


def limited_reply(question):
    """Answer the question unless a usage limit is reached, in which case explain the limit."""
    if st.session_state.asked >= MAX_PER_SESSION:
        return {"role": "assistant", "notice": True,
                "content": f"You've reached the limit of {MAX_PER_SESSION} questions for this "
                           "session. Thanks for trying the assistant!"}
    if not take_daily_slot():
        return {"role": "assistant", "notice": True,
                "content": "The assistant has reached its daily question limit. "
                           "Please come back tomorrow."}
    st.session_state.asked += 1
    with st.spinner("Searching the policies and writing an answer..."):
        return answer(question)


def main():
    """Password gate, data check, then sidebar, chat history and the new question."""
    global rag
    st.set_page_config(page_title="Coverage policy assistant", page_icon="💊")
    load_settings()
    password_gate()                 # stops here until unlocked
    try:
        ensure_data()
    except RuntimeError as e:
        st.error(str(e))
        st.stop()
    with st.spinner("Starting up (first load takes about 30 seconds)..."):
        import rag                  # binds the module-level name, once per server process
    st.title("Coverage policy assistant")
    st.caption("Repatha · Prolia · Otezla, from Aetna, Cigna and UnitedHealthcare policies "
               "and FDA labels. Each question is answered on its own.")
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("asked", 0)

    example = sidebar()
    warm_up()
    for message in st.session_state.messages:
        render(message)

    question = st.chat_input("Ask about Repatha, Prolia or Otezla coverage...") or example
    if question:
        user_message = {"role": "user", "content": question}
        render(user_message)
        reply = limited_reply(question)
        render(reply)
        st.session_state.messages += [user_message, reply]


main()
