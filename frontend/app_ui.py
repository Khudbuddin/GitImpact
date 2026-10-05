import os
import re
import requests
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="GitImpact | Codebase Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for modern, polished UI
st.markdown("""
<style>
    /* Metric Card */
    .metric-box {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 12px 16px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-val {
        font-size: 1.6rem;
        font-weight: 800;
        color: #38bdf8;
    }
    .metric-lbl {
        font-size: 0.72rem;
        text-transform: uppercase;
        color: #94a3b8;
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    /* Tech Stack Badges */
    .tech-pill {
        display: inline-block;
        background: linear-gradient(135deg, #312e81 0%, #1e1b4b 100%);
        color: #c7d2fe;
        border: 1px solid #4338ca;
        border-radius: 14px;
        padding: 3px 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 2px 4px 4px 0;
    }
    /* Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        border: 1px solid #3730a3;
        border-radius: 14px;
        padding: 24px 28px;
        margin-bottom: 24px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
    }
    /* Callout Card */
    .callout-card {
        background: #111827;
        border-left: 4px solid #6366f1;
        padding: 12px 16px;
        border-radius: 6px;
        margin: 10px 0;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 **Welcome to GitImpact Intelligence!**\n\n"
                "I am your AI codebase intelligence assistant. You can chat freely with me, or paste a "
                "public **GitHub repository link** (e.g. `https://github.com/owner/repo`) to inspect "
                "its real Abstract Syntax Tree (AST), file dependencies, directory mappings, and change blast radius."
            )
        }
    ]

if "repo_data" not in st.session_state:
    st.session_state.repo_data = None

if "repo_name" not in st.session_state:
    st.session_state.repo_name = None

if "quick_prompt" not in st.session_state:
    st.session_state.quick_prompt = None


def is_github_url(text: str) -> bool:
    """Detects if a string is or contains a GitHub repository URL."""
    pattern = r'https?://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+'
    return bool(re.search(pattern, text.strip()))


def extract_github_url(text: str) -> str:
    """Extracts the first GitHub repository URL from text."""
    match = re.search(r'https?://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', text.strip())
    return match.group(0) if match else text.strip()


def trigger_clone_analysis(url: str):
    """Sends repository to backend for cloning, AST scanning, and graph building."""
    clean_url = extract_github_url(url)
    with st.spinner(f"📥 Cloning & AST parsing **{clean_url}**..."):
        try:
            response = requests.post(f"{BACKEND_URL}/clone", json={"repo_url": clean_url}, timeout=120)
            data = response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to connect to backend: {e}. Is FastAPI running?"}

    return data


def render_interactive_graph(edges: list, nodes: list, graph_type="files"):
    """Builds a physics-based interactive HTML graph using PyVis."""
    net = Network(height="580px", width="100%", bgcolor="#0f172a", font_color="#f8fafc", directed=True)
    net.force_atlas_2based(gravity=-60, central_gravity=0.015, spring_length=120, damping=0.9)

    added_nodes = set()
    for n in nodes:
        label = os.path.basename(n.split("::")[0])
        if "::" in n:
            label += f"\n({n.split('::')[-1]})"
            color = "#34d399"  # emerald for functions
            size = 14
        else:
            color = "#38bdf8"  # cyan for files
            size = 20

        net.add_node(n, label=label, title=n, color=color, size=size)
        added_nodes.add(n)

    for u, v in edges:
        if u in added_nodes and v in added_nodes:
            net.add_edge(u, v, color="#64748b", arrows="to")

    try:
        html = net.generate_html()
        components.html(html, height=600, scrolling=True)
    except Exception as e:
        st.warning(f"Could not render interactive graph: {e}")


# --- SIDEBAR COMPONENT ---
with st.sidebar:
    st.markdown("## ⚡ **GitImpact**")
    st.caption("AI-Powered Code Dependency & Impact Intelligence")
    st.divider()

    if st.session_state.repo_data:
        data = st.session_state.repo_data
        st.subheader(f"📦 {data['repo_name']}")
        st.caption(f"Author: `{data.get('owner', 'Unknown')}`")

        # 4-Metric Grid
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-val">{data.get('total_files_parsed', 0)}</div>
                <div class="metric-lbl">Code Files</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-val">{data.get('graph_summary', {}).get('total_functions', 0)}</div>
                <div class="metric-lbl">Functions</div>
            </div>
            """, unsafe_allow_html=True)

        col3, col4 = st.columns(2)
        with col3:
            st.markdown(f"""
            <div class="metric-box" style="margin-top:6px;">
                <div class="metric-val">{data.get('graph_summary', {}).get('total_imports', 0)}</div>
                <div class="metric-lbl">Imports</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="metric-box" style="margin-top:6px;">
                <div class="metric-val">{data.get('graph_summary', {}).get('total_calls', 0)}</div>
                <div class="metric-lbl">Calls</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Tech Stack Badges
        tech_list = data.get("tech_stack", [])
        if tech_list:
            st.markdown("**Tech Stack:**")
            pills = "".join([f'<span class="tech-pill">{t}</span>' for t in tech_list])
            st.markdown(f"<div>{pills}</div>", unsafe_allow_html=True)

        st.divider()

        # One-Click Quick Prompts
        st.markdown("**⚡ Quick Prompts**")
        if st.button("📌 Explain Entire Project", use_container_width=True):
            st.session_state.quick_prompt = "Explain the whole repo, its architecture, and purpose"
            st.rerun()

        if st.button("📁 Which Directory Does What?", use_container_width=True):
            st.session_state.quick_prompt = "Which directory does what? Explain the folder structure."
            st.rerun()

        if st.button("🔗 How Are Files Connected?", use_container_width=True):
            st.session_state.quick_prompt = "How are files connected and how does data flow between functions?"
            st.rerun()

        if st.button("📑 Explain All 24 Files One-by-One", use_container_width=True):
            st.session_state.quick_prompt = "Explain each file in the given repo one by one"
            st.rerun()

        st.divider()

        # Directory Explorer
        directories = data.get("directories", {})
        if directories:
            with st.expander("🗂️ **Directory Explorer**", expanded=False):
                for dir_name, dir_info in directories.items():
                    st.markdown(f"📁 **`{dir_name}/`** — *{dir_info['purpose']}*")
                    for fname in dir_info.get("files", [])[:10]:
                        st.caption(f"  └─ `{fname}`")
                    if len(dir_info.get("files", [])) > 10:
                        st.caption(f"  └─ *...+{len(dir_info['files']) - 10} more*")

        st.divider()
        if st.button("🔄 Analyze Another Repo", use_container_width=True, type="secondary"):
            st.session_state.repo_data = None
            st.session_state.repo_name = None
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Repository cleared. Ready for a new conversation or GitHub link!"
            })
            st.rerun()

    else:
        st.info("ℹ️ **No repository loaded yet**\n\nEnter any public GitHub repo URL on the main page or in chat.")
        st.markdown("💡 **Supported AST Parsers:**\n- Python (`.py`)\n- Java (`.java`)\n- SQL (`.sql`)")


# --- MAIN TABS WORKSPACE ---
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
    st.header("⚡ GitImpact Intelligence Chat")

    # If no repo is loaded, show Hero Banner & Quick Form
    if not st.session_state.repo_name:
        st.markdown("""
        <div class="hero-banner">
            <h3 style="color: #f8fafc; margin-top:0;">🔍 Analyze Any Public GitHub Repository</h3>
            <p style="color: #cbd5e1; margin-bottom: 12px; font-size: 0.95rem;">
                Paste any repository link to extract real AST dependency graphs, understand folder architecture,
                trace exact function-to-function call pipelines, and simulate change blast radius.
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("quick_repo_form", clear_on_submit=True):
            col_in, col_bt = st.columns([5, 1])
            with col_in:
                input_url = st.text_input(
                    "GitHub Repository URL",
                    placeholder="https://github.com/owner/repository",
                    label_visibility="collapsed"
                )
            with col_bt:
                submitted = st.form_submit_button("Analyze", use_container_width=True, type="primary")

            if submitted and input_url:
                st.session_state.quick_prompt = input_url
                st.rerun()

    # Render Conversation Messages
    for msg in st.session_state.messages:
        avatar = "⚡" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if msg.get("diagram"):
                with st.expander("📊 View Architecture Flowchart (Mermaid)", expanded=False):
                    st.code(msg["diagram"], language="mermaid")

    # User Input Field
    user_input = st.chat_input("Ask anything about this repo (or paste a GitHub URL)...")

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
            # Case 1: Input is a GitHub URL
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
                            f"✅ **Analyzed repository `{data['repo_name']}` successfully!**\n\n"
                            f"- 📁 **Files Parsed:** `{total_files}` code files | `{total_funcs}` user-defined functions\n"
                            f"- 🛠️ **Tech Stack:** {techs}\n"
                            f"- 🚀 **Key Entry Points:** `{entry_pts}`\n\n"
                            f"**What would you like to explore next?**\n"
                            f"1. *'Explain the whole repo and its purpose'* 📌\n"
                            f"2. *'Which directory does what?'* 📁\n"
                            f"3. *'How are files and functions connected?'* 🔗\n"
                            f"4. *'Explain each file one by one'* 📑\n"
                            f"5. *'What breaks if I change [function or file]?'* 💥"
                        )
                        diag = data.get("mermaid_diagram")

                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply, "diagram": diag})
                st.rerun()

            # Case 2: Freeform Question
            else:
                with st.spinner("Analyzing codebase..."):
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
        st.subheader("🕸️ Interactive Dependency Network Graph")
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
        st.subheader("📂 Codebase & Function Inspector")
        st.caption("Inspect any real file in the codebase, review its functions, and see who calls it.")

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
                st.markdown(f"### 📄 `{f_info['basename']}`")
                st.markdown(f"**Path:** `{f_info['path']}` | **Directory:** `{f_info['directory']}`")

                funcs = f_info.get("functions", [])
                if funcs:
                    st.markdown(f"#### ⚙️ User-Defined Functions ({len(funcs)})")
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
        st.subheader("💥 Change Blast-Radius Simulator")
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