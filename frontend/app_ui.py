import os
import re
import requests
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

BACKEND_URL = "http://127.0.0.1:8000"

# --- PAGE CONFIGURATION (WIDE, NO SIDEBAR) ---
st.set_page_config(
    page_title="GitImpact | Codebase Intelligence Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- MODERN ENTERPRISE SAAS STYLING (MATCHING REFERENCE DESIGNS) ---
st.markdown("""
<style>
    /* Global Base */
    .stApp {
        background-color: #080c16;
        color: #f8fafc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", sans-serif;
    }

    /* Total Removal of Streamlit Sidebar */
    [data-testid="stSidebar"], [data-testid="collapsedControl"], section[data-testid="stSidebar"] {
        display: none !important;
    }

    /* Screen-wide container with generous padding */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2.2rem !important;
        padding-right: 2.2rem !important;
        max-width: 100% !important;
    }

    /* Top Executive Header Bar */
    .top-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: linear-gradient(90deg, #0d1424 0%, #151f38 50%, #0d1424 100%);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 14px;
        padding: 14px 28px;
        margin-bottom: 22px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
    }
    .brand-title {
        font-size: 1.45rem;
        font-weight: 800;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .brand-sub {
        font-size: 0.85rem;
        font-weight: 500;
        color: #94a3b8;
        letter-spacing: 0;
        margin-left: 6px;
    }
    .status-badge-online {
        background: rgba(16, 185, 129, 0.12);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.35);
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .status-badge-offline {
        background: rgba(239, 68, 68, 0.12);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.35);
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }

    /* Active Project Metadata Bar */
    .repo-active-bar {
        background: #0d1424;
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 14px;
        padding: 16px 24px;
        margin-bottom: 22px;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
    }
    .repo-active-title {
        font-size: 1.3rem;
        font-weight: 800;
        color: #f8fafc;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .metric-badge {
        background: #151f38;
        color: #94a3b8;
        border: 1px solid #233152;
        border-radius: 8px;
        padding: 7px 14px;
        font-size: 0.84rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .metric-badge strong {
        color: #38bdf8;
    }
    .tech-pill {
        background: rgba(99, 102, 241, 0.18);
        color: #c7d2fe;
        border: 1px solid rgba(99, 102, 241, 0.4);
        border-radius: 12px;
        padding: 3px 10px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    /* WIDE EXECUTIVE TABS COMPONENT (100% SCREEN WIDTH) */
    .stTabs [data-baseweb="tab-list"] {
        width: 100% !important;
        display: flex !important;
        background-color: #0b101d !important;
        padding: 6px !important;
        border-radius: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
        margin-bottom: 24px !important;
        gap: 8px !important;
    }
    .stTabs [data-baseweb="tab"] {
        flex: 1 !important;
        height: 52px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: transparent !important;
        border-radius: 10px !important;
        color: #94a3b8 !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        padding: 0 20px !important;
        transition: all 0.25s ease !important;
        border: 1px solid transparent !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #f8fafc !important;
        background: rgba(255, 255, 255, 0.04) !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1e1b4b 0%, #2e1065 100%) !important;
        color: #ffffff !important;
        border: 1px solid rgba(129, 140, 248, 0.5) !important;
        box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3) !important;
    }

    /* Modern Hero Container (Matching Reference Designs) */
    .hero-container {
        background: radial-gradient(circle at 10% 20%, #1e1b4b 0%, #0d1424 60%, #080c16 100%);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 18px;
        padding: 50px 45px;
        margin-bottom: 28px;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6);
        text-align: center;
    }
    .hero-eyebrow {
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: #818cf8;
        margin-bottom: 12px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(99, 102, 241, 0.14);
        padding: 4px 14px;
        border-radius: 20px;
        border: 1px solid rgba(99, 102, 241, 0.3);
    }
    .hero-title {
        font-size: 2.8rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 14px;
        line-height: 1.15;
    }
    .hero-subtitle {
        font-size: 1.15rem;
        color: #94a3b8;
        max-width: 820px;
        margin: 0 auto 32px auto;
        line-height: 1.6;
    }

    /* Feature Pills Row (Like Reference 2) */
    .feature-pills-row {
        display: flex;
        justify-content: center;
        gap: 16px;
        flex-wrap: wrap;
        margin-top: 24px;
    }
    .feature-pill-card {
        background: #0f182c;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 10px 18px;
        font-size: 0.85rem;
        color: #94a3b8;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .feature-pill-card strong {
        color: #f1f5f9;
    }

    /* Stepper Progress Bar (Like Reference 1) */
    .stepper-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        max-width: 860px;
        margin: 36px auto 0 auto;
        padding: 16px 24px;
        background: rgba(15, 24, 44, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
    }
    .step-item {
        display: flex;
        align-items: center;
        gap: 10px;
        text-align: left;
    }
    .step-num {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #1e1b4b;
        color: #c7d2fe;
        border: 1px solid rgba(99, 102, 241, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.85rem;
        font-weight: 700;
    }
    .step-text-title {
        font-size: 0.88rem;
        font-weight: 600;
        color: #f1f5f9;
    }
    .step-text-sub {
        font-size: 0.75rem;
        color: #64748b;
    }

    /* Message Bubbles */
    .stChatMessage {
        border-radius: 12px !important;
        margin-bottom: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        background-color: #0d1424 !important;
        padding: 18px !important;
    }

    /* Primary and Secondary Buttons */
    .stButton>button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
</style>
""", unsafe_allow_html=True)


# --- STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 **Welcome to GitImpact Codebase Intelligence Studio!**\n\n"
                "I am your AI codebase intelligence assistant. You can chat freely with me, or analyze any "
                "public **GitHub repository** to automatically build real AST dependency graphs, "
                "trace function-level execution pipelines, and simulate change blast radius with zero hallucinations."
            )
        }
    ]

if "repo_data" not in st.session_state:
    st.session_state.repo_data = None

if "repo_name" not in st.session_state:
    st.session_state.repo_name = None

if "quick_prompt" not in st.session_state:
    st.session_state.quick_prompt = None


# --- HELPER FUNCTIONS ---
def check_backend_health() -> bool:
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


def is_github_url(text: str) -> bool:
    pattern = r'https?://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+'
    return bool(re.search(pattern, text.strip()))


def extract_github_url(text: str) -> str:
    match = re.search(r'https?://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', text.strip())
    return match.group(0) if match else text.strip()


def trigger_clone_analysis(url: str):
    clean_url = extract_github_url(url)
    with st.spinner(f"📥 Cloning repository & parsing AST for **{clean_url}**..."):
        try:
            response = requests.post(f"{BACKEND_URL}/clone", json={"repo_url": clean_url}, timeout=150)
            if response.status_code != 200:
                return {"error": f"Server error {response.status_code}: {response.text}"}
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to connect to backend: {e}. Please ensure FastAPI is running on port 8000."}


def render_interactive_graph(edges: list, nodes: list, graph_type="files"):
    """Renders a wide, interactive physics graph with PyVis."""
    net = Network(height="680px", width="100%", bgcolor="#080c16", font_color="#f8fafc", directed=True)
    net.force_atlas_2based(gravity=-60, central_gravity=0.015, spring_length=140, damping=0.9)

    added_nodes = set()
    for n in nodes:
        label = os.path.basename(n.split("::")[0])
        if "::" in n:
            label += f"\n({n.split('::')[-1]})"
            color = "#10b981"  # Emerald for functions
            size = 15
        else:
            color = "#06b6d4"  # Cyan for files
            size = 22

        net.add_node(n, label=label, title=n, color=color, size=size)
        added_nodes.add(n)

    for u, v in edges:
        if u in added_nodes and v in added_nodes:
            net.add_edge(u, v, color="#475569", arrows="to")

    try:
        html = net.generate_html()
        components.html(html, height=700, scrolling=True)
    except Exception as e:
        st.warning(f"Could not render interactive graph: {e}")


# --- TOP EXECUTIVE NAVIGATION HEADER ---
backend_online = check_backend_health()
status_html = (
    '<div class="status-badge-online">🟢 Engine Online (Port 8000)</div>'
    if backend_online else
    '<div class="status-badge-offline">🔴 Backend Offline — Run uvicorn app.main:app</div>'
)

st.markdown(f"""
<div class="top-header">
    <div class="brand-title">
        ⚡ GitImpact <span class="brand-sub">Codebase Intelligence Studio</span>
    </div>
    {status_html}
</div>
""", unsafe_allow_html=True)


# =========================================================================
# VIEW 1: HERO LANDING SCREEN (WHEN NO REPOSITORY IS LOADED)
# Only ONE single search bar exists here. NO second chat input!
# =========================================================================
if not st.session_state.repo_data:
    st.markdown("""
    <div class="hero-container">
        <div class="hero-eyebrow">✦ CODEBASE INTELLIGENCE & AST DEPENDENCY ENGINE ✦</div>
        <div class="hero-title">Understand any codebase in under a minute.</div>
        <div class="hero-subtitle">
            Paste any public GitHub repository to extract real Abstract Syntax Trees (AST), map module dependencies,
            trace concrete function call pipelines, and simulate change blast radius with zero hallucinations.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Clean, Single Full-Width Input Box
    col_in, col_btn = st.columns([5, 1])
    with col_in:
        repo_input = st.text_input(
            "Repository URL Input",
            placeholder="Paste public GitHub repository link (e.g. https://github.com/owner/repository)",
            label_visibility="collapsed"
        )
    with col_btn:
        analyze_clicked = st.button("⚡ Analyze Repository →", use_container_width=True, type="primary")

    # Feature Pills (Matching Reference 2)
    st.markdown("""
    <div class="feature-pills-row">
        <div class="feature-pill-card">⚡ <strong>AST Grounded</strong> — Concrete AST parsing for Python & Java</div>
        <div class="feature-pill-card">🕸️ <strong>Topology Graph</strong> — Interactive force-directed dependency maps</div>
        <div class="feature-pill-card">💥 <strong>Blast Radius</strong> — Reverse-BFS impact simulation before commit</div>
    </div>
    """, unsafe_allow_html=True)

    # 4-Step Stepper (Matching Reference 1)
    st.markdown("""
    <div class="stepper-container">
        <div class="step-item">
            <div class="step-num">1</div>
            <div>
                <div class="step-text-title">Ingest & Clone</div>
                <div class="step-text-sub">Fetches repo files safely</div>
            </div>
        </div>
        <div style="color:#334155;">⟶</div>
        <div class="step-item">
            <div class="step-num">2</div>
            <div>
                <div class="step-text-title">AST Parsing</div>
                <div class="step-text-sub">Extracts functions & calls</div>
            </div>
        </div>
        <div style="color:#334155;">⟶</div>
        <div class="step-item">
            <div class="step-num">3</div>
            <div>
                <div class="step-text-title">Graph Assembly</div>
                <div class="step-text-sub">Builds call topology</div>
            </div>
        </div>
        <div style="color:#334155;">⟶</div>
        <div class="step-item">
            <div class="step-num">4</div>
            <div>
                <div class="step-text-title">Intelligence Studio</div>
                <div class="step-text-sub">Explore & chat</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if analyze_clicked and repo_input:
        if is_github_url(repo_input):
            data = trigger_clone_analysis(repo_input)
            if "error" in data:
                st.error(f"❌ Analysis Failed: {data['error']}")
            else:
                st.session_state.repo_data = data
                st.session_state.repo_name = data["repo_name"]

                techs = ", ".join(data.get("tech_stack", [])) or "Python"
                entry_pts = ", ".join(data.get("entry_points", [])) or "main.py"
                total_files = data.get("total_files_parsed", 0)
                total_funcs = data.get("graph_summary", {}).get("total_functions", 0)

                reply = (
                    f"✅ **Analyzed `{data['repo_name']}` successfully!**\n\n"
                    f"- 📁 **Files Parsed:** `{total_files}` code files | `{total_funcs}` user-defined functions\n"
                    f"- 🛠️ **Tech Stack:** {techs}\n"
                    f"- 🚀 **Key Entry Points:** `{entry_pts}`\n\n"
                    f"**What would you like to explore?** Use the quick action buttons above or ask:\n"
                    f"1. *'Explain the whole repo and its purpose'* 📌\n"
                    f"2. *'Which directory does what?'* 📁\n"
                    f"3. *'How are files and functions connected?'* 🔗\n"
                    f"4. *'Explain all files one by one'* 📑\n"
                    f"5. *'What breaks if I change [function or file]?'* 💥"
                )
                diag = data.get("mermaid_diagram")
                st.session_state.messages.append({
                    "role": "user",
                    "content": f"Analyze repository {extract_github_url(repo_input)}"
                })
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": reply,
                    "diagram": diag
                })
                st.rerun()
        else:
            st.warning("Please enter a valid public GitHub URL (e.g. `https://github.com/owner/repo`).")


# =========================================================================
# VIEW 2: WORKSPACE STUDIO (WHEN REPOSITORY IS LOADED)
# Contains the active metadata bar, 4 wide tabs, and the anchored chat input.
# =========================================================================
else:
    data = st.session_state.repo_data
    col_bar_info, col_bar_btn = st.columns([5, 1])

    with col_bar_info:
        tech_tags = "".join([f'<span class="tech-pill">{t}</span> ' for t in data.get("tech_stack", [])])
        st.markdown(f"""
        <div class="repo-active-bar">
            <div>
                <div class="repo-active-title">
                    📦 {data['repo_name']} <span style="font-size:0.85rem; color:#94a3b8; font-weight:400;">by {data.get('owner', 'Unknown')}</span>
                </div>
                <div style="margin-top: 8px;">{tech_tags}</div>
            </div>
            <div style="display:flex; gap:10px; flex-wrap:wrap;">
                <div class="metric-badge">📁 Files: <strong>{data.get('total_files_parsed', 0)}</strong></div>
                <div class="metric-badge">⚙️ Functions: <strong>{data.get('graph_summary', {}).get('total_functions', 0)}</strong></div>
                <div class="metric-badge">📦 Imports: <strong>{data.get('graph_summary', {}).get('total_imports', 0)}</strong></div>
                <div class="metric-badge">🔗 Calls: <strong>{data.get('graph_summary', {}).get('total_calls', 0)}</strong></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_bar_btn:
        st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Switch Project", use_container_width=True, type="secondary"):
            st.session_state.repo_data = None
            st.session_state.repo_name = None
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Repository cleared. Ready to analyze any new public GitHub project!"
            })
            st.rerun()

    # The 4 Wide Tabs
    tab_chat, tab_graph, tab_inspect, tab_impact = st.tabs([
        "💬 AI Intelligence Chat",
        "🕸️ Interactive Dependency Graph",
        "📂 Codebase & Function Explorer",
        "💥 Change Blast-Radius Simulator"
    ])

    # -------------------------------------------------------------
    # TAB 1: AI INTELLIGENCE CHAT (WIDE, WITH ANCHORED CHAT INPUT)
    # -------------------------------------------------------------
    with tab_chat:
        st.markdown("<p style='color:#94a3b8; font-size:0.85rem; margin-bottom:8px;'>⚡ <strong>Quick Intelligence Prompts:</strong></p>", unsafe_allow_html=True)
        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        with col_p1:
            if st.button("📌 Project Architecture", use_container_width=True):
                st.session_state.quick_prompt = "Explain the whole repo, its architecture, and purpose"
                st.rerun()
        with col_p2:
            if st.button("📁 Directory Responsibilities", use_container_width=True):
                st.session_state.quick_prompt = "Which directory does what? Explain the folder structure."
                st.rerun()
        with col_p3:
            if st.button("🌳 Function Call Hierarchy", use_container_width=True):
                st.session_state.quick_prompt = "Give me the tree chart or anything that shows how functions connected"
                st.rerun()
        with col_p4:
            if st.button("📑 Explain All Files One-by-One", use_container_width=True):
                st.session_state.quick_prompt = "Explain each file in the given repo one by one"
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # 1. Render all prior conversation messages
        for msg in st.session_state.messages:
            avatar = "⚡" if msg["role"] == "assistant" else "👤"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])
                if msg.get("diagram"):
                    with st.expander("📊 View Architecture Flowchart (Mermaid)", expanded=True):
                        st.markdown(f"```mermaid\n{msg['diagram']}\n```")

        # 2. Chat Input ALWAYS at the bottom of the message stream
        user_input = st.chat_input("Ask anything about this codebase (or paste another GitHub repository URL)...")

        # Determine prompt
        prompt_to_process = None
        if st.session_state.quick_prompt:
            prompt_to_process = st.session_state.quick_prompt
            st.session_state.quick_prompt = None
        elif user_input:
            prompt_to_process = user_input

        # 3. Handle prompt submission and IMMEDIATELY trigger rerun so input stays at bottom
        if prompt_to_process:
            st.session_state.messages.append({"role": "user", "content": prompt_to_process})

            if is_github_url(prompt_to_process):
                with st.spinner("Analyzing new repository..."):
                    new_data = trigger_clone_analysis(prompt_to_process)
                    if "error" in new_data:
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"❌ **Analysis Failed:** {new_data['error']}"
                        })
                    else:
                        st.session_state.repo_data = new_data
                        st.session_state.repo_name = new_data["repo_name"]
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"✅ **Analyzed `{new_data['repo_name']}` successfully!**",
                            "diagram": new_data.get("mermaid_diagram")
                        })
            else:
                with st.spinner("Reasoning over AST codebase catalog..."):
                    try:
                        payload = {
                            "repo_name": st.session_state.repo_name,
                            "message": prompt_to_process
                        }
                        response = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=90)
                        if response.status_code == 200:
                            resp_data = response.json()
                            reply = resp_data.get("answer", resp_data.get("error", "No response."))
                            diag = resp_data.get("diagram")
                        else:
                            reply = f"⚠️ Backend error ({response.status_code}): {response.text}"
                            diag = None
                    except Exception as e:
                        reply = f"⚠️ Could not connect to backend server: {e}"
                        diag = None

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": reply,
                    "diagram": diag
                })

            # RERUN GUARANTEES CHAT INPUT STAYS AT THE BOTTOM BELOW NEW MESSAGES
            st.rerun()

    # -------------------------------------------------------------
    # TAB 2: INTERACTIVE DEPENDENCY GRAPH
    # -------------------------------------------------------------
    with tab_graph:
        col_g1, col_g2 = st.columns([3, 1])
        with col_g1:
            st.markdown("### 🕸️ **Interactive Dependency Network Graph**")
            st.caption("Drag nodes, hover over files/functions to inspect metadata, and zoom to explore graph topology.")
        with col_g2:
            graph_mode = st.radio(
                "Graph Granularity:",
                ["File-Level Imports", "Function Call Graph"],
                horizontal=True
            )

        catalog = st.session_state.repo_data.get("catalog", {})
        if graph_mode == "File-Level Imports":
            file_edges = st.session_state.repo_data.get("file_level_edges", [])
            file_nodes = [f["full_path"] for f in catalog.get("files", [])]
            render_interactive_graph(file_edges, file_nodes, graph_type="files")
        else:
            call_edges = catalog.get("call_edges", [])
            func_nodes = [f["full_path"] + "::" + fn for f in catalog.get("files", []) for fn in f.get("functions", [])]
            render_interactive_graph(call_edges, func_nodes, graph_type="functions")

    # -------------------------------------------------------------
    # TAB 3: CODEBASE & FUNCTION EXPLORER
    # -------------------------------------------------------------
    with tab_inspect:
        st.markdown("### 📂 **Codebase & Function Explorer**")
        st.caption("Inspect parsed user-defined functions, callers, callees, and source code.")

        catalog = st.session_state.repo_data.get("catalog", {})
        files = catalog.get("files", [])

        if not files:
            st.info("No code files found in this repository.")
        else:
            col_list, col_detail = st.columns([1, 2])

            with col_list:
                file_options = {f["path"]: f for f in files}
                selected_file_path = st.selectbox(
                    "Select Code File:",
                    options=list(file_options.keys()),
                    format_func=lambda p: f"📄 {p} ({len(file_options[p]['functions'])} funcs)"
                )
                selected_file = file_options[selected_file_path]

                st.markdown(f"**Directory:** `{selected_file.get('directory', 'Root')}`")
                st.markdown(f"**Lines of Code:** `{selected_file.get('lines', 0)}`")
                st.markdown(f"**Imports Count:** `{len(selected_file.get('imports', []))}`")

                funcs = selected_file.get("functions", [])
                st.markdown(f"#### User-Defined Functions ({len(funcs)})")
                if funcs:
                    for fn in funcs:
                        st.markdown(f"- ⚙️ **`{fn}`**")
                else:
                    st.caption("No standalone user-defined functions in this file.")

            with col_detail:
                st.markdown(f"#### 📄 Source Preview: `{selected_file_path}`")
                raw_path = selected_file["full_path"]
                if os.path.exists(raw_path):
                    try:
                        with open(raw_path, "r", encoding="utf-8", errors="ignore") as f:
                            code_content = f.read()
                        ext = selected_file_path.split(".")[-1]
                        lang = "python" if ext == "py" else ("java" if ext == "java" else "sql")
                        st.code(code_content, language=lang, line_numbers=True)
                    except Exception as e:
                        st.error(f"Could not read file: {e}")
                else:
                    st.warning("File content preview not available.")

    # -------------------------------------------------------------
    # TAB 4: CHANGE BLAST-RADIUS SIMULATOR
    # -------------------------------------------------------------
    with tab_impact:
        st.markdown("### 💥 **Change Blast-Radius Simulator**")
        st.caption("Simulate reverse dependency propagation to identify exactly what would break before modifying a function or file.")

        catalog = st.session_state.repo_data.get("catalog", {})
        files = catalog.get("files", [])
        functions = catalog.get("functions", [])

        col_sim1, col_sim2 = st.columns([3, 1])

        with col_sim1:
            options = []
            for fn in functions:
                options.append(f"⚙️ Function: {fn['name']} ({fn['file']})")
            for f in files:
                options.append(f"📄 File: {f['path']}")

            selected_target = st.selectbox(
                "Select Function or File to Modify:",
                options=options
            )

        with col_sim2:
            depth = st.slider("Traversal Depth (Hops):", min_value=1, max_value=5, value=3)

        if st.button("🚀 Calculate Blast Radius", type="primary", use_container_width=True):
            with st.spinner("Traversing dependency graph via Reverse-BFS..."):
                if selected_target.startswith("⚙️ Function:"):
                    raw_fn_name = selected_target.split("⚙️ Function:")[1].split("(")[0].strip()
                    query_msg = f"What breaks if I change function {raw_fn_name}?"
                else:
                    raw_file_name = selected_target.split("📄 File:")[1].strip()
                    query_msg = f"What breaks if I modify file {raw_file_name}?"

                payload = {
                    "repo_name": st.session_state.repo_name,
                    "message": query_msg
                }
                try:
                    res = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=90)
                    if res.status_code == 200:
                        impact_res = res.json()
                        st.markdown(impact_res.get("answer", "No impact analysis returned."))
                        if impact_res.get("diagram"):
                            with st.expander("📊 View Blast-Radius Impact Flowchart", expanded=True):
                                st.markdown(f"```mermaid\n{impact_res['diagram']}\n```")
                    else:
                        st.error(f"Backend error: {res.text}")
                except Exception as e:
                    st.error(f"Failed to query impact simulation: {e}")