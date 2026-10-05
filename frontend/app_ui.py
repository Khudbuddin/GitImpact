import os
import re
import requests
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

BACKEND_URL = "http://127.0.0.1:8000"

# Configure wide, expansive layout with collapsed sidebar for maximum screen estate
st.set_page_config(
    page_title="GitImpact | Codebase Intelligence Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom High-End SaaS Theme — Obsidian, Electric Cyan & Indigo
st.markdown("""
<style>
    /* Global Base */
    .stApp {
        background-color: #070a12;
        color: #f8fafc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", sans-serif;
    }

    /* Hide default Streamlit sidebar toggle clutter if desired */
    [data-testid="stSidebar"] {
        display: none;
    }

    /* Executive Top Bar */
    .top-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: linear-gradient(90deg, #0f172a 0%, #161f36 50%, #0f172a 100%);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 12px;
        padding: 14px 28px;
        margin-bottom: 20px;
        box-shadow: 0 8px 24px -4px rgba(0, 0, 0, 0.45);
    }
    .brand-title {
        font-size: 1.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
    }
    .status-badge-online {
        background: rgba(16, 185, 129, 0.12);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .status-badge-offline {
        background: rgba(239, 68, 68, 0.12);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    /* Full-Width Project Control Bar */
    .project-banner {
        background: #0f172a;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px 24px;
        margin-bottom: 20px;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
    }
    .project-info-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #f1f5f9;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .pill-metric {
        background: #1e293b;
        color: #94a3b8;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 6px 14px;
        font-size: 0.82rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .pill-metric strong {
        color: #38bdf8;
    }
    .tech-tag {
        background: rgba(99, 102, 241, 0.15);
        color: #a5b4fc;
        border: 1px solid rgba(99, 102, 241, 0.35);
        border-radius: 12px;
        padding: 3px 10px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    /* Wide Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        width: 100%;
        display: flex;
        justify-content: space-around;
        background-color: #0d1322;
        padding: 8px 12px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        flex: 1;
        text-align: center;
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 600;
        font-size: 0.95rem;
        padding: 12px 20px;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #f1f5f9;
        background-color: rgba(255, 255, 255, 0.03);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1e1b4b 0%, #2e1065 100%) !important;
        color: #c7d2fe !important;
        border: 1px solid rgba(99, 102, 241, 0.5) !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
    }

    /* Hero Search Card */
    .hero-card {
        background: radial-gradient(circle at 10% 20%, #1e1b4b 0%, #0f172a 60%, #070a12 100%);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 16px;
        padding: 40px 48px;
        margin-bottom: 28px;
        box-shadow: 0 16px 36px -8px rgba(0, 0, 0, 0.6);
        text-align: center;
    }
    .hero-title {
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #f8fafc 0%, #cbd5e1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 12px;
    }
    .hero-desc {
        font-size: 1.1rem;
        color: #94a3b8;
        max-width: 780px;
        margin: 0 auto 24px auto;
        line-height: 1.6;
    }

    /* Feature Highlights in Hero */
    .feature-card {
        background: #0f172a;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 20px;
        text-align: left;
    }
    .feature-card h4 {
        color: #38bdf8;
        margin-top: 0;
        font-size: 1.05rem;
    }
    .feature-card p {
        color: #94a3b8;
        font-size: 0.85rem;
        margin-bottom: 0;
        line-height: 1.5;
    }

    /* Message Bubbles */
    .stChatMessage {
        border-radius: 12px;
        margin-bottom: 14px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 **Welcome to GitImpact Intelligence Studio!**\n\n"
                "I am your AI codebase intelligence assistant. You can chat freely with me, or paste any "
                "public **GitHub repository link** above to automatically build real AST dependency graphs, "
                "trace function-level execution pipelines, and simulate change blast radius."
            )
        }
    ]

if "repo_data" not in st.session_state:
    st.session_state.repo_data = None

if "repo_name" not in st.session_state:
    st.session_state.repo_name = None

if "quick_prompt" not in st.session_state:
    st.session_state.quick_prompt = None


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
    with st.spinner(f"📥 Cloning & AST Parsing **{clean_url}**..."):
        try:
            response = requests.post(f"{BACKEND_URL}/clone", json={"repo_url": clean_url}, timeout=150)
            if response.status_code != 200:
                return {"error": f"Server error {response.status_code}: {response.text}"}
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to connect to backend: {e}. Ensure FastAPI is running on port 8000."}


def render_interactive_graph(edges: list, nodes: list, graph_type="files"):
    """Builds a wide physics-based interactive HTML graph using PyVis."""
    net = Network(height="650px", width="100%", bgcolor="#070a12", font_color="#f8fafc", directed=True)
    net.force_atlas_2based(gravity=-55, central_gravity=0.015, spring_length=130, damping=0.9)

    added_nodes = set()
    for n in nodes:
        label = os.path.basename(n.split("::")[0])
        if "::" in n:
            label += f"\n({n.split('::')[-1]})"
            color = "#10b981"  # emerald
            size = 15
        else:
            color = "#06b6d4"  # cyan
            size = 22

        net.add_node(n, label=label, title=n, color=color, size=size)
        added_nodes.add(n)

    for u, v in edges:
        if u in added_nodes and v in added_nodes:
            net.add_edge(u, v, color="#475569", arrows="to")

    try:
        html = net.generate_html()
        components.html(html, height=670, scrolling=True)
    except Exception as e:
        st.warning(f"Could not render interactive graph: {e}")


# --- TOP EXECUTIVE NAVIGATION BAR ---
backend_online = check_backend_health()
status_html = (
    '<div class="status-badge-online">🟢 Engine Online (Port 8000)</div>'
    if backend_online else
    '<div class="status-badge-offline">🔴 Backend Offline — Run: uvicorn app.main:app --port 8000</div>'
)

st.markdown(f"""
<div class="top-header">
    <div class="brand-title">⚡ GitImpact <span style="font-size:0.85rem; font-weight:500; color:#94a3b8;">Codebase Intelligence Studio</span></div>
    {status_html}
</div>
""", unsafe_allow_html=True)


# --- REPOSITORY HEADER OR HERO BANNER ---
if st.session_state.repo_data:
    data = st.session_state.repo_data
    col_b1, col_b2 = st.columns([4, 1])

    with col_b1:
        tech_tags = "".join([f'<span class="tech-tag">{t}</span> ' for t in data.get("tech_stack", [])])
        st.markdown(f"""
        <div class="project-banner">
            <div>
                <div class="project-info-title">📦 {data['repo_name']} <span style="font-size:0.85rem; color:#94a3b8; font-weight:400;">by {data.get('owner', 'Unknown')}</span></div>
                <div style="margin-top: 8px;">{tech_tags}</div>
            </div>
            <div style="display:flex; gap:10px; flex-wrap:wrap;">
                <div class="pill-metric">📁 Files: <strong>{data.get('total_files_parsed', 0)}</strong></div>
                <div class="pill-metric">⚙️ Functions: <strong>{data.get('graph_summary', {}).get('total_functions', 0)}</strong></div>
                <div class="pill-metric">📦 Imports: <strong>{data.get('graph_summary', {}).get('total_imports', 0)}</strong></div>
                <div class="pill-metric">🔗 Calls: <strong>{data.get('graph_summary', {}).get('total_calls', 0)}</strong></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_b2:
        if st.button("🔄 Switch Project", use_container_width=True, type="secondary"):
            st.session_state.repo_data = None
            st.session_state.repo_name = None
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Repository cleared. Ready to analyze a new project or continue chatting!"
            })
            st.rerun()

else:
    # Full Width Hero State
    st.markdown("""
    <div class="hero-card">
        <div class="hero-title">Deep Codebase Intelligence in Seconds</div>
        <div class="hero-desc">
            Paste any GitHub repository link to extract real Abstract Syntax Tree (AST) dependency graphs,
            trace exact function-to-function execution pipelines, and simulate change blast radius with zero hallucinations.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_in, col_btn = st.columns([5, 1])
    with col_in:
        repo_input = st.text_input(
            "Repository URL",
            placeholder="Paste public GitHub URL (e.g. https://github.com/Khudbuddin/Smart-Expense-Categorizer)",
            label_visibility="collapsed"
        )
    with col_btn:
        analyze_clicked = st.button("🚀 Analyze Repo", use_container_width=True, type="primary")

    # Quick Demo Buttons
    st.markdown("<p style='color:#94a3b8; font-size:0.85rem; margin-top:8px;'>💡 <strong>Quick Demos:</strong> Click to analyze instantly:</p>", unsafe_allow_html=True)
    col_d1, col_d2, col_d3 = st.columns([1, 1, 3])
    with col_d1:
        if st.button("📦 Smart-Expense-Categorizer", use_container_width=True):
            st.session_state.quick_prompt = "https://github.com/Khudbuddin/Smart-Expense-Categorizer"
            st.rerun()
    with col_d2:
        if st.button("🔮 vedaz-ai", use_container_width=True):
            st.session_state.quick_prompt = "https://github.com/Khudbuddin/vedaz-ai"
            st.rerun()

    if analyze_clicked and repo_input:
        st.session_state.quick_prompt = repo_input
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)


# --- 4 WIDE TABS WORKSPACE ---
if st.session_state.repo_data:
    tab_chat, tab_graph, tab_inspect, tab_impact = st.tabs([
        "💬 Intelligence Chat",
        "🕸️ Interactive Graph",
        "📂 Code & Function Explorer",
        "💥 Change Blast-Radius Simulator"
    ])
else:
    tab_chat = st.container()
    tab_graph = None
    tab_inspect = None
    tab_impact = None


# ==========================================
# TAB 1: INTELLIGENCE CHAT (WIDE)
# ==========================================
with tab_chat:
    # If a repo is active, show quick action prompt pills right above the chat
    if st.session_state.repo_data:
        st.markdown("<p style='color:#94a3b8; font-size:0.85rem; margin-bottom:6px;'>⚡ <strong>Quick Intelligence Prompts:</strong></p>", unsafe_allow_html=True)
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
            if st.button("🔗 Function Pipelines & Flow", use_container_width=True):
                st.session_state.quick_prompt = "How are files connected and how does data flow between functions?"
                st.rerun()
        with col_p4:
            if st.button("📑 Explain All Files One-by-One", use_container_width=True):
                st.session_state.quick_prompt = "Explain each file in the given repo one by one"
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

    # Render Conversation Messages
    for msg in st.session_state.messages:
        avatar = "⚡" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if msg.get("diagram"):
                with st.expander("📊 View Architecture Flowchart (Mermaid)", expanded=False):
                    st.code(msg["diagram"], language="mermaid")

    user_input = st.chat_input("Ask anything about this codebase (or paste a GitHub URL)...")

    if st.session_state.quick_prompt:
        prompt_to_process = st.session_state.quick_prompt
        st.session_state.quick_prompt = None
    elif user_input:
        prompt_to_process = user_input
    else:
        prompt_to_process = None

    if prompt_to_process:
        st.session_state.messages.append({"role": "user", "content": prompt_to_process})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt_to_process)

        with st.chat_message("assistant", avatar="⚡"):
            if is_github_url(prompt_to_process):
                with st.status("Analyzing Repository...", expanded=True) as status:
                    st.write("📥 Cloning repository files from GitHub...")
                    data = trigger_clone_analysis(prompt_to_process)
                    if "error" in data:
                        status.update(label="Analysis failed", state="error")
                        reply = f"❌ **Analysis Failed:** {data['error']}"
                        diag = None
                    else:
                        st.write("🌳 Parsing AST, extracting function calls & indexing directories...")
                        st.session_state.repo_data = data
                        st.session_state.repo_name = data["repo_name"]

                        techs = ", ".join(data.get("tech_stack", [])) or "Python"
                        entry_pts = ", ".join(data.get("entry_points", [])) or "main.py"
                        total_files = data.get("total_files_parsed", 0)
                        total_funcs = data.get("graph_summary", {}).get("total_functions", 0)

                        status.update(label="Repository Analyzed Successfully!", state="complete")
                        reply = (
                            f"✅ **Analyzed `{data['repo_name']}` successfully!**\n\n"
                            f"- 📁 **Files Parsed:** `{total_files}` code files | `{total_funcs}` user-defined functions\n"
                            f"- 🛠️ **Tech Stack:** {techs}\n"
                            f"- 🚀 **Key Entry Points:** `{entry_pts}`\n\n"
                            f"**What would you like to explore next?** Use the quick action buttons above or ask:\n"
                            f"1. *'Explain the whole repo and its purpose'* 📌\n"
                            f"2. *'Which directory does what?'* 📁\n"
                            f"3. *'How are files and functions connected?'* 🔗\n"
                            f"4. *'Explain all files one by one'* 📑\n"
                            f"5. *'What breaks if I change [function or file]?'* 💥"
                        )
                        diag = data.get("mermaid_diagram")

                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply, "diagram": diag})
                st.rerun()

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

                st.markdown(reply)
                if diag:
                    with st.expander("📊 View Architecture Flowchart (Mermaid)", expanded=False):
                        st.code(diag, language="mermaid")

                st.session_state.messages.append({"role": "assistant", "content": reply, "diagram": diag})


# ==========================================
# TAB 2: INTERACTIVE GRAPH (FULL 100% WIDTH)
# ==========================================
if tab_graph and st.session_state.repo_data:
    with tab_graph:
        col_g1, col_g2 = st.columns([3, 1])
        with col_g1:
            st.markdown("### 🕸️ **Interactive Dependency Network Graph**")
            st.caption("Drag nodes, hover over files/functions, and zoom in/out to explore dependencies.")
        with col_g2:
            graph_mode = st.radio(
                "Graph View:",
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


# ==========================================
# TAB 3: CODE & FUNCTION EXPLORER (WIDE)
# ==========================================
if tab_inspect and st.session_state.repo_data:
    with tab_inspect:
        st.markdown("### 📂 **Codebase & Function Explorer**")
        st.caption("Select any real file in the codebase to inspect all its user-defined functions, line numbers, and callers.")

        catalog = st.session_state.repo_data.get("catalog", {})
        files_list = catalog.get("files", [])
        file_options = {f["path"]: f for f in files_list}

        col_sel1, col_sel2 = st.columns([3, 1])
        with col_sel1:
            selected_file_path = st.selectbox(
                "Select a file to inspect:",
                options=list(file_options.keys()),
                help="Select any real parsed file from this repository"
            )

        if selected_file_path:
            f_info = file_options[selected_file_path]
            col_f1, col_f2 = st.columns([3, 1])

            with col_f1:
                st.markdown(f"#### 📄 `{f_info['basename']}`")
                st.markdown(f"**Path:** `{f_info['path']}` | **Directory:** `{f_info['directory']}`")

                funcs = f_info.get("functions", [])
                if funcs:
                    st.markdown(f"**⚙️ User-Defined Functions ({len(funcs)}):**")
                    for fn in funcs:
                        st.markdown(f"- 🔹 **`def {fn}(...)`**")
                else:
                    st.info("This file does not define standalone functions (it may contain configuration, models, or entrypoint code).")

                imports = f_info.get("imports", [])
                if imports:
                    with st.expander(f"📦 Imports ({len(imports)})", expanded=False):
                        for imp in imports:
                            st.code(imp, language="python")

            with col_f2:
                st.markdown("#### ⚡ Quick Actions")
                if st.button(f"🔍 Explain {f_info['basename']}", use_container_width=True):
                    st.session_state.quick_prompt = f"Explain the file {f_info['path']} and its functions"
                    st.rerun()

                if st.button(f"💥 Impact of {f_info['basename']}", use_container_width=True):
                    st.session_state.quick_prompt = f"What breaks if I change {f_info['basename']}?"
                    st.rerun()


# ==========================================
# TAB 4: BLAST-RADIUS SIMULATOR (WIDE)
# ==========================================
if tab_impact and st.session_state.repo_data:
    with tab_impact:
        st.markdown("### 💥 **Change Blast-Radius Simulator**")
        st.caption("Select any function or file to simulate the exact downstream ripple effects and risk.")

        catalog = st.session_state.repo_data.get("catalog", {})
        all_functions = [fn["id"] for fn in catalog.get("functions", [])]
        all_files = [f["path"] for f in catalog.get("files", [])]
        target_options = sorted(all_functions + all_files)

        col_s1, col_s2 = st.columns([3, 1])
        with col_s1:
            selected_target = st.selectbox(
                "Select target function or file to modify:",
                options=target_options,
                help="Choose a component to compute reverse BFS dependents"
            )
        with col_s2:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            run_sim = st.button("🚀 Run Blast Simulation", type="primary", use_container_width=True)

        if run_sim and selected_target:
            with st.spinner(f"Tracing blast radius for `{selected_target}`..."):
                try:
                    payload = {
                        "repo_name": st.session_state.repo_name,
                        "message": f"What breaks if I modify {selected_target}?"
                    }
                    resp = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=60).json()
                    st.markdown(resp.get("answer", "No response."))
                except Exception as e:
                    st.error(f"Failed to run simulation: {e}")