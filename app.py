import os
import json
import streamlit as st
from dotenv import load_dotenv
from doc_parser import process_file
from search_engine import build_index, search
from score_optimizer import rerank
from generator import stream_answer
from utils import format_context, truncate_context
from eval.retrieval_eval import run_retrieval_eval, TEST_SET
from eval.answer_eval import run_answer_eval
from eval.ragas_eval import run_ragas_eval

load_dotenv()

st.set_page_config(layout="wide", page_title="NeuralDoc Search", page_icon="🔍", initial_sidebar_state="expanded")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    [data-testid="collapsedControl"] {display: none !important;}

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    /* Dark background for entire app */
    .stApp {
        background: linear-gradient(135deg, #0a0a0f 0%, #0d1117 50%, #0a0a1a 100%) !important;
        background-attachment: fixed !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        min-width: 300px !important;
        max-width: 300px !important;
        transform: none !important;
        visibility: visible !important;
        display: block !important;
        background: linear-gradient(180deg, #0d1117 0%, #111827 100%) !important;
        border-right: 1px solid rgba(99,102,241,0.2) !important;
    }
    section[data-testid="stSidebar"] > div {
        width: 300px !important;
    }
    div[data-testid="stSidebarContent"] {
        background: transparent !important;
        padding: 1.2rem !important;
    }

    .block-container {
        padding-top: 1rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100% !important;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.3px !important;
        padding: 0.55rem 1rem !important;
        transition: all 0.25s ease !important;
        box-shadow: 0 0 15px rgba(99,102,241,0.3) !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
        box-shadow: 0 0 25px rgba(99,102,241,0.6) !important;
        transform: translateY(-1px) !important;
    }

    /* Inputs */
    .stTextInput > div > div > input, .stTextArea textarea {
        border-radius: 8px !important;
        border: 1px solid rgba(99,102,241,0.3) !important;
        background: rgba(255,255,255,0.04) !important;
        color: #e2e8f0 !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stTextInput > div > div > input:focus, .stTextArea textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 2px rgba(99,102,241,0.2) !important;
    }

    /* Selectbox */
    .stSelectbox > div > div {
        border-radius: 8px !important;
        border: 1px solid rgba(99,102,241,0.3) !important;
        background: rgba(255,255,255,0.04) !important;
        color: #e2e8f0 !important;
    }

    /* Expander */
    .stExpander {
        border: 1px solid rgba(99,102,241,0.2) !important;
        border-radius: 10px !important;
        background: rgba(255,255,255,0.02) !important;
    }
    .stExpander summary {
        color: #a5b4fc !important;
    }

    /* Chat messages */
    .stChatMessage {
        border-radius: 14px !important;
        border: 1px solid rgba(99,102,241,0.15) !important;
        background: rgba(255,255,255,0.03) !important;
        backdrop-filter: blur(10px) !important;
        margin-bottom: 0.5rem !important;
    }

    /* Chat input */
    .stChatInput textarea {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(99,102,241,0.35) !important;
        border-radius: 12px !important;
        color: #f1f5f9 !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stChatInput textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 20px rgba(99,102,241,0.3) !important;
    }

    /* Alerts */
    .stAlert {
        border-radius: 10px !important;
        border: 1px solid rgba(99,102,241,0.2) !important;
        background: rgba(99,102,241,0.07) !important;
    }

    /* Divider */
    hr {
        border-color: rgba(99,102,241,0.15) !important;
        margin: 0.8rem 0 !important;
    }

    /* Metrics */
    [data-testid="metric-container"] {
        background: rgba(99,102,241,0.08) !important;
        border: 1px solid rgba(99,102,241,0.2) !important;
        border-radius: 10px !important;
        padding: 1rem !important;
    }
    [data-testid="metric-container"] label {
        color: #a5b4fc !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #f1f5f9 !important;
        font-weight: 700 !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255,255,255,0.03) !important;
        border-radius: 10px !important;
        gap: 0.25rem !important;
        padding: 0.3rem !important;
        border: 1px solid rgba(99,102,241,0.15) !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important;
        color: #94a3b8 !important;
        font-weight: 500 !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: #fff !important;
        box-shadow: 0 0 15px rgba(99,102,241,0.4) !important;
    }

    /* Dataframe */
    [data-testid="stDataFrame"] {
        border: 1px solid rgba(99,102,241,0.2) !important;
        border-radius: 10px !important;
    }

    /* Spinner */
    .stSpinner > div {
        border-top-color: #6366f1 !important;
    }

    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #6366f1, #8b5cf6) !important;
        border-radius: 50px !important;
    }

    /* Sliders */
    .stSlider [data-testid="stThumbValue"] {
        color: #6366f1 !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: #0d1117; }
    ::-webkit-scrollbar-thumb { background: #6366f1; border-radius: 10px; }

    /* Radio */
    .stRadio label { color: #cbd5e1 !important; }
    .stRadio [data-testid="stMarkdownContainer"] p { color: #cbd5e1 !important; }

    /* Caption/text */
    .stMarkdown p, .stText, label, p { color: #cbd5e1 !important; }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: #f1f5f9 !important; }

    /* File uploader */
    [data-testid="stFileUploader"] {
        background: rgba(99,102,241,0.05) !important;
        border: 2px dashed rgba(99,102,241,0.3) !important;
        border-radius: 12px !important;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: rgba(99,102,241,0.6) !important;
        background: rgba(99,102,241,0.08) !important;
    }
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "chunks" not in st.session_state:
    st.session_state.chunks = []
if "bm25_index" not in st.session_state:
    st.session_state.bm25_index = None
if "retrieval_eval_result" not in st.session_state:
    st.session_state.retrieval_eval_result = None
if "answer_eval_result" not in st.session_state:
    st.session_state.answer_eval_result = None
if "ragas_eval_result" not in st.session_state:
    st.session_state.ragas_eval_result = None

with st.sidebar:
    st.markdown("<h2 style='font-size:1.1rem; font-weight:700; color:#1a1a1a; margin-bottom:0;'>NeuralDoc Search</h2>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.72rem; color:#64748b; margin-top:2px; text-transform:uppercase; letter-spacing:0.8px;'>BM25 + Reranker + Inference Engine</p>", unsafe_allow_html=True)
    st.divider()

    st.markdown("<p style='font-size:0.72rem; color:#64748b; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;'>Documents</p>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader("Upload", type=["pdf", "txt"], accept_multiple_files=True, label_visibility="collapsed")

    with st.expander("Chunking Settings", expanded=False):
        chunk_size = st.slider("Chunk size (words)", 100, 500, 300)
        top_k = st.slider("BM25 top-k", 10, 50, 20)
        top_n = st.slider("Rerank top-n", 3, 10, 5)

    if st.button("Index Documents", use_container_width=True):
        if uploaded_files:
            all_chunks = []
            progress = st.progress(0)
            for i, f in enumerate(uploaded_files):
                st.caption(f"Processing {f.name}...")
                chunks = process_file(f, chunk_size=chunk_size)
                all_chunks.extend(chunks)
                progress.progress((i + 1) / len(uploaded_files))
            st.session_state.chunks = all_chunks
            st.session_state.bm25_index = build_index(all_chunks)
            st.success(f"{len(all_chunks)} chunks indexed from {len(uploaded_files)} file(s)")
        else:
            st.warning("Upload at least one file first.")

    st.divider()
    st.markdown("<p style='font-size:0.72rem; color:#64748b; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;'>Groq Settings</p>", unsafe_allow_html=True)

    st.text_input("API Key (Managed by Backend)", type="password", value="••••••••••••••••••••", disabled=True, label_visibility="collapsed")
    api_key = os.getenv("GROQ_API_KEY", "")

    model = st.selectbox("Model", [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ], label_visibility="collapsed")

    with st.expander("Advanced Settings", expanded=False):
        temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.1)

    st.divider()
    if st.button("Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.markdown("<p style='font-size:0.72rem; color:#64748b; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;'>Mode</p>", unsafe_allow_html=True)
    app_mode = st.radio("Mode", ["Chat", "Evaluate"], label_visibility="collapsed")

# ── Evaluate mode ──
if app_mode == "Evaluate":
    st.markdown("<h2 style='font-size:1.3rem; font-weight:700;'>Evaluation</h2>", unsafe_allow_html=True)
    has_data = "chunks" in st.session_state and st.session_state.chunks

    eval_tab1, eval_tab2, eval_tab3 = st.tabs(["Retrieval eval", "Answer eval", "RAGAS"])

    # ── TAB 1: Retrieval eval ──
    with eval_tab1:
        st.info("**Recall@k** measures the fraction of relevant documents found in the top-k results. "
                "**Precision@k** measures how many of the top-k results are actually relevant.")

        if not has_data:
            st.warning("Upload and index a document first to run retrieval evaluation.")
        else:
            if st.button("Run retrieval eval", key="run_retrieval"):
                with st.spinner("Running retrieval evaluation..."):
                    st.session_state.retrieval_eval_result = run_retrieval_eval(
                        st.session_state.chunks, st.session_state.bm25_index
                    )

            if st.session_state.retrieval_eval_result:
                res = st.session_state.retrieval_eval_result
                col1, col2 = st.columns(2)
                col1.metric("Avg Recall@5", f"{res['avg_recall']:.3f}")
                col2.metric("Avg Precision@5", f"{res['avg_precision']:.3f}")

                import pandas as pd
                df = pd.DataFrame(res["per_query"])
                df.columns = ["Query", "Recall@5", "Precision@5"]
                st.dataframe(df, use_container_width=True)

        st.markdown("**Current TEST_SET** (edit `eval/retrieval_eval.py` to add real chunk IDs):")
        st.code(json.dumps(TEST_SET, indent=2), language="json")

    # ── TAB 2: Answer eval ──
    with eval_tab2:
        st.info("**Faithfulness** measures whether the answer is supported by the provided context. "
                "**Relevancy** measures how well the answer addresses the question.")

        placeholder_json = json.dumps([{
            "question": "What is the main topic?",
            "answer": "The document discusses...",
            "context": "The main topic of this paper is..."
        }], indent=2)

        qa_input = st.text_area(
            "Paste QA pairs as JSON array",
            value=placeholder_json,
            height=200,
            key="answer_eval_input",
        )

        if st.button("Run answer eval", key="run_answer"):
            if not api_key:
                st.error("Groq API key is required for answer evaluation.")
            else:
                try:
                    qa_pairs = json.loads(qa_input)
                    with st.spinner("Running answer evaluation (LLM-based scoring)..."):
                        st.session_state.answer_eval_result = run_answer_eval(qa_pairs, api_key)
                except json.JSONDecodeError:
                    st.error("Malformed JSON. Please provide a valid JSON array.")
                except Exception as e:
                    st.error(f"Evaluation failed: {e}")

        if st.session_state.answer_eval_result:
            res = st.session_state.answer_eval_result
            col1, col2 = st.columns(2)
            col1.metric("Avg Faithfulness", f"{res['avg_faithfulness']:.3f}")
            col2.metric("Avg Relevancy", f"{res['avg_relevancy']:.3f}")

            import pandas as pd
            df = pd.DataFrame(res["per_question"])
            df.columns = ["Question", "Faithfulness", "Relevancy"]
            st.dataframe(df, use_container_width=True)

    # ── TAB 3: RAGAS ──
    with eval_tab3:
        st.info("**RAGAS** (Retrieval Augmented Generation Assessment) evaluates your RAG pipeline with 4 metrics: "
                "faithfulness, answer_relevancy, context_recall, and context_precision. "
                "Requires the `ragas` and `datasets` packages.")
        st.code("pip install ragas datasets", language="bash")

        ragas_placeholder = json.dumps([{
            "question": "What is the main topic?",
            "answer": "The document discusses...",
            "contexts": ["The main topic of this paper is..."],
            "ground_truth": "The main topic is machine learning."
        }], indent=2)

        ragas_input = st.text_area(
            "Paste QA pairs as JSON array (with ground_truth)",
            value=ragas_placeholder,
            height=220,
            key="ragas_eval_input",
        )

        if st.button("Run RAGAS eval", key="run_ragas"):
            try:
                qa_pairs = json.loads(ragas_input)
                with st.spinner("Running RAGAS evaluation..."):
                    st.session_state.ragas_eval_result = run_ragas_eval(qa_pairs)
            except json.JSONDecodeError:
                st.error("Malformed JSON. Please provide a valid JSON array.")
            except Exception as e:
                st.error(f"Evaluation failed: {e}")

        if st.session_state.ragas_eval_result:
            res = st.session_state.ragas_eval_result
            if "error" in res:
                st.error(res["error"])
            else:
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Faithfulness", f"{res.get('faithfulness', 0):.3f}")
                col2.metric("Answer Relevancy", f"{res.get('answer_relevancy', 0):.3f}")
                col3.metric("Context Recall", f"{res.get('context_recall', 0):.3f}")
                col4.metric("Context Precision", f"{res.get('context_precision', 0):.3f}")
                st.balloons()

    st.stop()

# ── Chat mode ──
if not st.session_state.messages and st.session_state.bm25_index is None:
    st.components.v1.html("""
<!DOCTYPE html>
<html>
<head>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html, body { width: 100%; height: 100%; background: #080b14; overflow: hidden; font-family: 'Inter', sans-serif; }
  canvas { position: fixed; top: 0; left: 0; width: 100% !important; height: 100% !important; }
  .page {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    display: flex; align-items: center; justify-content: center;
    z-index: 10; padding: 2rem; gap: 2.5rem;
  }
  .left { flex: 1.2; padding-right: 1rem; }
  .badge {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: rgba(99,102,241,0.12); border: 1px solid rgba(99,102,241,0.35);
    border-radius: 999px; padding: 0.28rem 0.85rem;
    font-size: 0.68rem; font-weight: 600; letter-spacing: 0.8px;
    color: #a5b4fc; text-transform: uppercase; margin-bottom: 1rem;
  }
  .badge-dot { width: 6px; height: 6px; background: #6366f1; border-radius: 50%; animation: blink 1.8s ease infinite; display: inline-block; }
  h1 {
    font-size: 3.4rem; font-weight: 800; line-height: 1.08;
    letter-spacing: -2px; margin-bottom: 0.7rem;
    background: linear-gradient(135deg, #fff 30%, #a5b4fc 70%, #818cf8);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  }
  .subtitle { font-size: 1rem; color: #94a3b8; line-height: 1.7; margin-bottom: 1.3rem; max-width: 440px; font-weight: 400; }
  .tags { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 1.4rem; }
  .tag {
    padding: 0.28rem 0.75rem; border: 1px solid rgba(99,102,241,0.35);
    border-radius: 6px; font-size: 0.68rem; color: #a5b4fc; font-weight: 500;
    background: rgba(99,102,241,0.07); backdrop-filter: blur(4px);
  }
  .hint { font-size: 0.78rem; color: #6366f1; font-weight: 500; display: flex; align-items: center; gap: 0.4rem; animation: glow 2.5s ease infinite; }
  .arrow { animation: slide 1.5s ease infinite; display: inline-block; }
  .right { flex: 1; display: flex; flex-direction: column; gap: 0.7rem; }
  .card {
    background: rgba(13,17,27,0.85); border: 1px solid rgba(99,102,241,0.18);
    border-radius: 14px; padding: 1.1rem 1.3rem; backdrop-filter: blur(16px);
    position: relative; overflow: hidden; transition: all 0.3s;
  }
  .card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(99,102,241,0.5), transparent);
  }
  .card:hover { border-color: rgba(99,102,241,0.4); transform: translateY(-2px); box-shadow: 0 8px 30px rgba(99,102,241,0.12); }
  .card-title {
    font-size: 0.62rem; text-transform: uppercase; letter-spacing: 1px;
    color: #6366f1; font-weight: 700; margin-bottom: 0.55rem;
    display: flex; align-items: center; gap: 0.4rem;
  }
  .card-title::before { content: ''; width: 3px; height: 10px; background: #6366f1; border-radius: 2px; display: block; }
  .card-text { font-size: 0.78rem; color: #94a3b8; line-height: 1.7; }
  .card-text strong { color: #c7d2fe; }
  .arch { display: flex; align-items: center; gap: 0.25rem; flex-wrap: wrap; }
  .arch-step {
    background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.2);
    border-radius: 6px; padding: 0.28rem 0.55rem; font-size: 0.67rem; color: #94a3b8; font-weight: 500;
  }
  .arch-step.accent { background: rgba(99,102,241,0.15); border-color: rgba(99,102,241,0.45); color: #a5b4fc; font-weight: 700; }
  .arch-arrow { font-size: 0.65rem; color: rgba(99,102,241,0.4); }
  .no-list { display: flex; flex-direction: column; gap: 0.38rem; }
  .no-row { font-size: 0.74rem; color: #64748b; display: flex; align-items: center; gap: 0.5rem; }
  .no-badge {
    background: rgba(239,68,68,0.12); color: #f87171;
    font-size: 0.58rem; font-weight: 800; padding: 0.1rem 0.4rem;
    border-radius: 4px; border: 1px solid rgba(239,68,68,0.2); letter-spacing: 0.5px;
  }
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }
  @keyframes glow { 0%,100%{text-shadow:0 0 8px rgba(99,102,241,0.3)} 50%{text-shadow:0 0 20px rgba(99,102,241,0.7)} }
  @keyframes slide { 0%,100%{transform:translateX(0)} 50%{transform:translateX(4px)} }
</style>
</head>
<body>
<canvas id="c"></canvas>
<div class="page">
  <div class="left">
    <div class="badge"><span class="badge-dot"></span>Built by Abhijeet Abhi &nbsp;&middot;&nbsp; AI Systems</div>
    <h1>NeuralDoc<br>Search</h1>
    <p class="subtitle">Precision document Q&amp;A without vector databases or embedding APIs &mdash; powered by sparse retrieval and semantic reranking.</p>
    <div class="tags">
      <span class="tag">BM25 Sparse Indexing</span>
      <span class="tag">Cross-Encoder Reranker</span>
      <span class="tag">Groq LLM</span>
      <span class="tag">RAGAS Evaluation</span>
      <span class="tag">Zero Infrastructure</span>
    </div>
    <div class="hint"><span class="arrow">&larr;</span> Upload a document in the sidebar to begin</div>
  </div>
  <div class="right">
    <div class="card">
      <div class="card-title">What is NeuralDoc Search?</div>
      <div class="card-text">
        Traditional RAG converts text into embeddings stored in a <strong>vector database</strong> requiring costly APIs. NeuralDoc Search uses <strong>BM25 sparse retrieval</strong> + a <strong>cross-encoder reranker</strong> to achieve the same precision at zero infra cost.
      </div>
    </div>
    <div class="card">
      <div class="card-title">System Architecture</div>
      <div class="arch">
        <div class="arch-step accent">PDF/TXT</div><div class="arch-arrow">&rarr;</div>
        <div class="arch-step">Chunker</div><div class="arch-arrow">&rarr;</div>
        <div class="arch-step accent">BM25 Index</div><div class="arch-arrow">&rarr;</div>
        <div class="arch-step">Top-20</div><div class="arch-arrow">&rarr;</div>
        <div class="arch-step accent">Reranker</div><div class="arch-arrow">&rarr;</div>
        <div class="arch-step">Top-5</div><div class="arch-arrow">&rarr;</div>
        <div class="arch-step accent">Groq LLM</div><div class="arch-arrow">&rarr;</div>
        <div class="arch-step">Answer</div>
      </div>
    </div>
    <div class="card">
      <div class="card-title">No Infrastructure Required</div>
      <div class="no-list">
        <div class="no-row"><span class="no-badge">NO</span> Vector database (Pinecone, Weaviate, Chroma)</div>
        <div class="no-row"><span class="no-badge">NO</span> Embedding model or external API</div>
        <div class="no-row"><span class="no-badge">NO</span> LangChain, LlamaIndex, or orchestration overhead</div>
      </div>
    </div>
  </div>
</div>
<script>
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
canvas.width = window.innerWidth; canvas.height = window.innerHeight;
const particles = [];
for(let i=0; i<120; i++){
  particles.push({
    x: Math.random()*canvas.width, y: Math.random()*canvas.height,
    vx: (Math.random()-0.5)*0.3, vy: (Math.random()-0.5)*0.3,
    r: Math.random()*1.5+0.3, alpha: Math.random()*0.5+0.1
  });
}
function draw(){
  ctx.clearRect(0,0,canvas.width,canvas.height);
  ctx.fillStyle='#080b14'; ctx.fillRect(0,0,canvas.width,canvas.height);
  for(let i=0;i<particles.length;i++){
    for(let j=i+1;j<particles.length;j++){
      const dx=particles[i].x-particles[j].x, dy=particles[i].y-particles[j].y;
      const dist=Math.sqrt(dx*dx+dy*dy);
      if(dist<130){
        ctx.beginPath(); ctx.moveTo(particles[i].x,particles[i].y); ctx.lineTo(particles[j].x,particles[j].y);
        ctx.strokeStyle='rgba(99,102,241,'+(0.18*(1-dist/130))+')'; ctx.lineWidth=0.6; ctx.stroke();
      }
    }
    ctx.beginPath(); ctx.arc(particles[i].x,particles[i].y,particles[i].r,0,Math.PI*2);
    ctx.fillStyle='rgba(99,102,241,'+particles[i].alpha+')';
    ctx.shadowBlur=8; ctx.shadowColor='rgba(99,102,241,0.6)'; ctx.fill(); ctx.shadowBlur=0;
    particles[i].x+=particles[i].vx; particles[i].y+=particles[i].vy;
    if(particles[i].x<0||particles[i].x>canvas.width) particles[i].vx*=-1;
    if(particles[i].y<0||particles[i].y>canvas.height) particles[i].vy*=-1;
  }
  const grd=ctx.createRadialGradient(canvas.width*0.3,canvas.height*0.5,0,canvas.width*0.3,canvas.height*0.5,canvas.width*0.35);
  grd.addColorStop(0,'rgba(99,102,241,0.06)'); grd.addColorStop(1,'rgba(0,0,0,0)');
  ctx.fillStyle=grd; ctx.fillRect(0,0,canvas.width,canvas.height);
  requestAnimationFrame(draw);
}
draw();
window.addEventListener('resize',()=>{ canvas.width=window.innerWidth; canvas.height=window.innerHeight; });
</script>
</body>
</html>
""", height=680, scrolling=False)

else:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

if st.session_state.bm25_index is None:
    st.stop()

if not api_key:
    st.error("Groq API key missing. Get one free at https://console.groq.com")
    st.stop()

query = st.chat_input("Ask a question about your documents...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.write(query)

    q_upper = query.upper()
    if "OPEN" in q_upper:
        if "ETHEREAL RETAIL" in q_upper:
            proj, link = "Ethereal Retail", "https://ethereal-retail.vercel.app"
        elif "CLARITYAI" in q_upper or "CLARITY AI" in q_upper:
            proj, link = "ClarityAI", "https://clarity-ai.vercel.app"
        elif "ECOCYCLE" in q_upper or "ECO CYCLE" in q_upper:
            proj, link = "EcoCycle", "https://eco-cycle.vercel.app"
        else:
            proj, link = None, None

        if proj and link:
            msg = f"Opening **{proj}** in a new tab... If popups are blocked, **[Click here to launch directly]({link})**!"
            st.components.v1.html(f"<script>window.parent.open('{link}', '_blank');</script>", height=0)
            st.session_state.messages.append({"role": "assistant", "content": msg})
            with st.chat_message("assistant"):
                st.markdown(msg)
            st.stop()

    with st.spinner("Retrieving..."):
        bm25_results = search(query, st.session_state.bm25_index, st.session_state.chunks, top_k=top_k)

    if not bm25_results:
        st.warning("No relevant chunks found.")
        st.stop()

    with st.spinner("Reranking..."):
        reranked = rerank(query, bm25_results, top_n=top_n)

    with st.expander("View retrieved chunks"):
        tab1, tab2 = st.tabs(["BM25 top results", "Reranked top results"])
        with tab1:
            for c in bm25_results:
                st.markdown(f"**Score:** `{c['bm25_score']:.4f}` | **Source:** `{c['source_file']}` | **Chunk:** `#{c['chunk_index']}`")
                st.caption(c["text"][:120] + "...")
                st.divider()
        with tab2:
            for c in reranked:
                st.markdown(f"**Rerank Score:** `{c['rerank_score']:.4f}` | **Source:** `{c['source_file']}` | **Chunk:** `#{c['chunk_index']}`")
                st.write(c["text"])
                st.divider()

    safe_chunks = truncate_context(reranked)
    context = format_context(safe_chunks)

    response, latency, used_model = stream_answer(query, context, api_key, model, temperature)

    st.session_state.messages.append({"role": "assistant", "content": response})

    st.markdown(f"<p style='color:#6366f1; font-size:0.78rem;'><code>{used_model}</code> &nbsp;|&nbsp; {latency}s</p>", unsafe_allow_html=True)