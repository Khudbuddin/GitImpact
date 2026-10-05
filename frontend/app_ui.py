import os
import re
import requests
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

BACKEND_URL = "http://127.0.0.1:8000"

# Configure modern wide layout
st.set_page_config(
    page_title="GitImpact | Codebase Intelligence Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End SaaS CSS Theme
st.markdown("""
<style>
    /* Global Base */
    .stApp {
        background-color: #080c14;
        color: #f1f5f9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Top Navigation Banner */
    .top-navbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: linear-gradient(90deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 12px;
        padding: 14px 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.5);
    }
    .brand-title {
        font-size: 1.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #60a5fa 0%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .status-badge-online {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .status-badge-offline {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
    }

    /* Modern Metric Cards */
    .stat-card {
        background: linear-gradient(145deg, #0f172a 0%, #172033 100%);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 10px;
        padding: 12px 14px;
        text-align: center;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .stat-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
        transform: translateY(-2px);
    }
    .stat-value {
        font-size: 1.7rem;
        font-weight: 800;
        color: #38bdf8;
        line-height: 1.2;
    }
    .stat-label {
        font-size: 0.7rem;
        text-transform: uppercase;
        color: #94a3b8;
        letter-spacing: 0.08em;
        margin-top: 4px;
        font-weight: 600;
    }

    /* Tech Stack Pills */
    .tech-pill {
        display: inline-block;
        background: rgba(99, 102, 241, 0.15);
        color: #c7d2fe;
        border: 1px solid rgba(99, 102, 241, 0.35);
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 2px 4px 4px 0;
    }

    /* Hero Search Section */
    .hero-card {
        background: radial-gradient(circle at top left, #1e1b4b 0%, #0f172a 60%, #080c14 100%);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 16px;
        padding: 32px 36px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }
    .hero-title {
        font-size: 2rem;
        font-weight: 800;
        color: #f8fafc;
        margin-bottom: 8px;
    }
    .hero-subtitle {
        font-size: 1rem;
        color: #94a3b8;
        margin-bottom: 20px;
        line-height: 1.5;
    }

    /* Action Chip Buttons */
    .chip-btn {
        background: #1e293b;
        color: #e2e8f0;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 0.85rem;
        cursor: pointer;
        display: inline-block;
        margin: 4px;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0b0f19;
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #0f172a;
        padding: 6px 10px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 600;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1e1b4b !important;
        color: #a5b4fc !important;
        border: 1px solid #4338ca !important;
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
    """Checks if the FastAPI server is reachable."""
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
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to connect to backend: {e}. Ensure FastAPI is running on port 8000."}


def render_interactive_graph(edges: list, nodes: list, graph_type="files"):
    """Builds a physics-based interactive HTML graph using PyVis."""
    net = Network(height="600px", width="100%", bgcolor="#090d16", font_color="#f8fafc", directed=True)
    net.force_atlas_2based(gravity=-60, central_gravity=0.015, spring_length=120, damping=0.9)

    added_nodes = set()
    for n in nodes:
        label = os.path.basename(n.split("::")[0])
        if "::" in n:
            label += f"\n({n.split('::')[-1]})"
            color = "#10b981"  # emerald
            size = 14
        else:
            color = "#06b6d4"  # cyan
            size = 20

        net.add_node(n, label=label, title=n, color=color, size=size)
        added_nodes.add(n)

    for u, v in edges:
        if u in added_nodes and v in added_nodes:
            net.add_edge(u, v, color="#475569", arrows="to")

    try:
        html = net.generate_html()
        components.html(html, height=620, scrolling=True)
    except Exception as e:
        st.warning(f"Could not render interactive graph: {e}")


# --- TOP GLOBAL BAR ---
backend_online = check_backend_health()
status_html = (
    '<div class="status-badge-online">🟢 Core Engine Online</div>'
    if backend_online else
    '<div class="status-badge-offline">🔴 Backend Offline (Start with uvicorn app.main:app)</div>'
)

st.markdown(f"""
<div class="top-navbar">
    <div class="brand-title">⚡ GitImpact <span style="font-size:0.85rem; font-weight:500; color:#94a3b8;">Codebase Intelligence Studio</span></div>
    {status_html}
</div>
""", unsafe_allow_html=True)


# --- SIDEBAR COMPONENT ---
with st.sidebar:
    st.markdown("### 🎛️ **Repository Hub**")

    if st.session_state.repo_data:
        data = st.session_state.repo_data
        st.markdown(f"**Active Project:** `{data['repo_name']}`")
        st.caption(f"Author: `{data.get('owner', 'Unknown')}`")

        # 4 Metric Cards Grid
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{data.get('total_files_parsed', 0)}</div>
                <div class="stat-label">Code Files</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{data.get('graph_summary', {}).get('total_functions', 0)}</div>
                <div class="stat-label">Functions</div>
            </div>
            """, unsafe_allow_html=True)

        col3, col4 = st.columns(2)
        with col3:
            st.markdown(f"""
            <div class="stat-card" style="margin-top:6px;">
                <div class="stat-value">{data.get('graph_summary', {}).get('total_imports', 0)}</div>
                <div class="stat-label">Imports</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="stat-card" style="margin-top:6px;">
                <div class="stat-value">{data.get('graph_summary', {}).get('total_calls', 0)}</div>
                <div class="stat-label">Calls</div>
            </div>
            """, unsafe_allow_html=True)

        # Tech Stack Badges
        tech_list = data.get("tech_stack", [])
        if tech_list:
            st.markdown("<br>**Tech Stack:**", unsafe_allow_html=True)
            pills = "".join([f'<span class="tech-pill">{t}</span>' for t in tech_list])
            st.markdown(f"<div>{pills}</div>", unsafe_allow_html=True)

        st.divider()

        # Prompt Palette
        st.markdown("**⚡ Intelligence Prompts**")
        if st.button("📌 Explain Entire Project", use_container_width=True):
            st.session_state.quick_prompt = "Explain the whole repo, its architecture, and purpose"
            st.rerun()

        if st.button("📁 Which Directory Does What?", use_container_width=True):
            st.session_state.quick_prompt = "Which directory does what? Explain the folder structure."
            st.rerun()

        if st.button("🔗 How Are Files & Functions Connected?", use_container_width=True):
            st.session_state.quick_prompt = "How are files connected and how does data flow between functions?"
            st.rerun()

        if st.button("📑 Explain All Files One-by-One", use_container_width=True):
            st.session_state.quick_prompt = "Explain each file in the given repo one by one"
            st.rerun()

        st.divider()

        # Collapsible Directory Explorer
        directories = data.get("directories", {})
        if directories:
            with st.expander("🗂️ **Directory Explorer**", expanded=False):
                for dir_name, dir_info in directories.items():
                    st.markdown(f"📁 **`{dir_name}/`** — *{dir_info['purpose']}*")
                    for fname in dir_info.get("files", [])[:8]:
                        st.caption(f"  └─ `{fname}`")
                    if len(dir_info.get("files", [])) > 8:
                        st.caption(f"  └─ *...+{len(dir_info['files']) - 8} more*")

        st.divider()
        if st.button("🔄 Switch Repository", use_container_width=True, type="secondary"):
            st.session_state.repo_data = None
            st.session_state.repo_name = None
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Repository cleared. Ready for a new conversation or GitHub link!"
            })
            st.rerun()

    else:
        st.info("ℹ️ **No active repository**\n\nEnter any public GitHub repo URL on the main page to analyze.")
        st.markdown("**Supported Parsers:**\n- Python (`.py`)\n- Java (`.java`)\n- SQL (`.sql`)")


# --- MAIN WORKSPACE ---
if not st.session_state.repo_name:
    # Modern Hero State
    st.markdown("""
    <div class="hero-card">
        <div class="hero-title">Deep Codebase Intelligence</div>
        <div class="hero-subtitle">
            Paste any GitHub repository link to extract real AST dependency graphs, understand folder architecture,
            trace exact function-to-function call pipelines, and simulate change blast radius.
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
        analyze_clicked = st.button("🚀 Analyze", use_container_width=True, type="primary")

    # Quick Demo Links
    st.caption("💡 **Quick Demo:** Click to try:")
    col_d1, col_d2, col_d3 = st.columns([1, 1, 3])
    with col_d1:
        if st.button("📦 Smart-Expense-Categorizer", use_container_width=True):
            st.session_state.quick_prompt = "https://github.com/Khudbuddin/Smart-Expense-Categorizer"
            st.rerun()
    with col_d2:
        if st.button("🌐 octocat/Hello-World", use_container_width=True):
            st.session_state.quick_prompt = "https://github.com/octocat/Hello-World"
            st.rerun()

    if analyze_clicked and repo_input:
        st.session_state.quick_prompt = repo_input
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)


# Tabs: Show full workspace tabs if a repo is loaded, otherwise single tab
if st.session_state.repo_data:
    tab_chat, tab_graph, tab_inspect, tab_impact = st.tabs([
        "💬 Intelligence Chat",
        "🕸️ Interactive Graph",
        "📂 File & Function Inspector",
        "💥 Blast-Radius Simulator"
    ])
else:
    tab_chat = st.container()
    tab_graph = None
    tab_inspect = None
    tab_impact = None


# ==========================================
# TAB 1: INTELLIGENCE CHAT
# ==========================================
with tab_chat:
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
                with st.status("Analyzing Codebase...", expanded=True) as status:
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
                            f"**What would you like to explore?**\n"
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
                        resp_data = response.json()
                        reply = resp_data.get("answer", resp_data.get("error", "An error occurred."))
                        diag = resp_data.get("diagram")
                    except requests.exceptions.RequestException as e:
                        reply = f"⚠️ Could not connect to backend server: {e}"
                        diag = None

                st.markdown(reply)
                if diag:
                    with st.expander("📊 View Architecture Flowchart (Mermaid)", expanded=False):
                        st.code(diag, language="mermaid")

                st.session_state.messages.append({"role": "assistant", "content": reply, "diagram": diag})


# ==========================================
# TAB 2: INTERACTIVE NETWORK GRAPH
# ==========================================
if tab_graph and st.session_state.repo_data:
    with tab_graph:
        st.markdown("### 🕸️ **Interactive Dependency Network Graph**")
        st.caption("Drag nodes, hover over files/functions, and zoom in/out to explore dependencies.")

        graph_mode = st.radio(
            "Graph View Mode:",
            ["File-Level Import Architecture", "Function-to-Function Call Graph"],
            horizontal=True
        )

        catalog = st.session_state.repo_data.get("catalog", {})
        if graph_mode == "File-Level Import Architecture":
            file_edges = st.session_state.repo_data.get("file_level_edges", [])
            file_nodes = [f["full_path"] for f in catalog.get("files", [])]
            render_interactive_graph(file_edges, file_nodes, graph_type="files")
        else:
            call_edges = catalog.get("call_edges", [])
            func_nodes = [f["full_path"] + "::" + fn for f in catalog.get("files", []) for fn in f.get("functions", [])]
            render_interactive_graph(call_edges, func_nodes, graph_type="functions")


# ==========================================
# TAB 3: FILE & FUNCTION INSPECTOR
# ==========================================
if tab_inspect and st.session_state.repo_data:
    with tab_inspect:
        st.markdown("### 📂 **Codebase & Function Inspector**")
        st.caption("Select any real file in the codebase to inspect all its user-defined functions, line numbers, and callers.")

        catalog = st.session_state.repo_data.get("catalog", {})
        files_list = catalog.get("files", [])
        file_options = {f["path"]: f for f in files_list}

        selected_file_path = st.selectbox(
            "Select a file to inspect:",
            options=list(file_options.keys()),
            help="Select any real parsed file from this repository"
        )

        if selected_file_path:
            f_info = file_options[selected_file_path]
            col_f1, col_f2 = st.columns([2, 1])

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
# TAB 4: BLAST-RADIUS SIMULATOR
# ==========================================
if tab_impact and st.session_state.repo_data:
    with tab_impact:
        st.markdown("### 💥 **Change Blast-Radius Simulator**")
        st.caption("Select any function or file to simulate the exact downstream ripple effects and risk.")

        catalog = st.session_state.repo_data.get("catalog", {})
        all_functions = [fn["id"] for fn in catalog.get("functions", [])]
        all_files = [f["path"] for f in catalog.get("files", [])]
        target_options = sorted(all_functions + all_files)

        selected_target = st.selectbox(
            "Select target function or file to modify:",
            options=target_options,
            help="Choose a component to compute reverse BFS dependents"
        )

        col_sim1, col_sim2 = st.columns([1, 4])
        with col_sim1:
            run_sim = st.button("🚀 Run Simulation", type="primary", use_container_width=True)

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