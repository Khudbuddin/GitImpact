import re
import requests
import streamlit as st

BACKEND_URL = "http://127.0.0.1:8000"

# Page configuration
st.set_page_config(
    page_title="GitImpact | Codebase Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    /* Metric Card Styling */
    .metric-card {
        background: #1e222d;
        border: 1px solid #2d3342;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
    }
    .metric-val {
        font-size: 1.4rem;
        font-weight: 700;
        color: #60a5fa;
    }
    .metric-lbl {
        font-size: 0.75rem;
        text-transform: uppercase;
        color: #94a3b8;
    }
    .badge {
        display: inline-block;
        background: #312e81;
        color: #c7d2fe;
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 2px;
    }
    .hero-banner {
        background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
        border: 1px solid #3730a3;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 **Welcome to GitImpact!**\n\n"
                "I am your AI code intelligence assistant. You can chat with me freely, or paste a "
                "public **GitHub repository link** (e.g. `https://github.com/owner/repo`) to analyze "
                "its architecture, directory structure, file connections, and change impact blast radius."
            )
        }
    ]

if "repo_data" not in st.session_state:
    st.session_state.repo_data = None

if "repo_name" not in st.session_state:
    st.session_state.repo_name = None

if "file_nodes" not in st.session_state:
    st.session_state.file_nodes = []

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
    with st.spinner(f"Cloning & parsing **{clean_url}** (AST, directories, dependency graph)..."):
        try:
            response = requests.post(f"{BACKEND_URL}/clone", json={"repo_url": clean_url}, timeout=120)
            data = response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to connect to backend: {e}. Is FastAPI running?"}

    return data


# --- SIDEBAR COMPONENT ---
with st.sidebar:
    st.title("⚡ GitImpact")
    st.caption("AI-Powered Code Dependency & Impact Intelligence")
    st.divider()

    if st.session_state.repo_data:
        data = st.session_state.repo_data
        st.subheader(f"📦 {data['repo_name']}")
        st.caption(f"Owner: `{data.get('owner', 'Unknown')}`")

        # Key Metrics Grid
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val">{data.get('total_files_parsed', 0)}</div>
                <div class="metric-lbl">Code Files</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val">{data.get('total_sql_files', 0)}</div>
                <div class="metric-lbl">SQL Files</div>
            </div>
            """, unsafe_allow_html=True)

        # Tech Stack Badges
        tech_list = data.get("tech_stack", [])
        if tech_list:
            st.markdown("**Tech Stack:**")
            badges_html = "".join([f'<span class="badge">{tech}</span>' for tech in tech_list])
            st.markdown(f"<div>{badges_html}</div>", unsafe_allow_html=True)

        st.divider()

        # One-Click Quick Action Prompts
        st.markdown("**⚡ Quick Prompts**")
        if st.button("📌 Explain Entire Project", use_container_width=True):
            st.session_state.quick_prompt = "Explain the whole repo and its purpose"
            st.rerun()

        if st.button("📁 Which Directory Does What?", use_container_width=True):
            st.session_state.quick_prompt = "Which directory does what? Explain the folder structure."
            st.rerun()

        if st.button("🔗 How Are Files Connected?", use_container_width=True):
            st.session_state.quick_prompt = "How are files connected and what is the architecture flow?"
            st.rerun()

        if st.button("🚀 Main Entry Points", use_container_width=True):
            st.session_state.quick_prompt = "What are the main entry points of this repository?"
            st.rerun()

        st.divider()

        # Collapsible Directory & File Explorer
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
        if st.button("🔄 Analyze Another Repository", use_container_width=True, type="secondary"):
            st.session_state.repo_data = None
            st.session_state.repo_name = None
            st.session_state.file_nodes = []
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Repository cleared. Ready for a new conversation or GitHub link!"
            })
            st.rerun()

    else:
        st.info("ℹ️ **No active repository**\n\nPaste a GitHub URL into the chat or the box on the main screen to begin deep analysis.")
        st.markdown("💡 **Supported Languages:**")
        st.markdown("- Python (`.py`) via Tree-Sitter AST\n- Java (`.java`) via Tree-Sitter AST\n- SQL (`.sql`) via SQLParse")


# --- MAIN VIEW ---
st.header("⚡ GitImpact Intelligence Chat")

# If no repo is loaded, show a quick URL input card
if not st.session_state.repo_name:
    st.markdown("""
    <div class="hero-banner">
        <h3>🔍 Analyze Any Public GitHub Repository</h3>
        <p style="color: #cbd5e1; margin-bottom: 12px;">
            Paste any repository URL to automatically extract AST dependency graphs, understand folder architecture,
            and inspect blast-radius change impacts.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("quick_repo_form", clear_on_submit=True):
        col_input, col_btn = st.columns([5, 1])
        with col_input:
            input_url = st.text_input(
                "GitHub Repository URL",
                placeholder="https://github.com/owner/repository",
                label_visibility="collapsed"
            )
        with col_btn:
            submitted = st.form_submit_button("Analyze", use_container_width=True, type="primary")

        if submitted and input_url:
            st.session_state.quick_prompt = input_url
            st.rerun()

# Render Message History
for msg in st.session_state.messages:
    avatar = "⚡" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg.get("diagram"):
            with st.expander("📊 View Dependency Architecture Diagram", expanded=True):
                st.code(msg["diagram"], language="mermaid")

# Handle User Input (either from chat input or quick prompt button)
user_input = st.chat_input("Ask anything about the codebase (or paste a GitHub repo URL)...")

if st.session_state.quick_prompt:
    prompt_to_process = st.session_state.quick_prompt
    st.session_state.quick_prompt = None
elif user_input:
    prompt_to_process = user_input
else:
    prompt_to_process = None

if prompt_to_process:
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt_to_process})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt_to_process)

    with st.chat_message("assistant", avatar="⚡"):
        # Case A: Input is a GitHub URL
        if is_github_url(prompt_to_process):
            with st.status("Analyzing Repository...", expanded=True) as status:
                st.write("📥 Cloning repository files from GitHub...")
                data = trigger_clone_analysis(prompt_to_process)
                if "error" in data:
                    status.update(label="Analysis failed", state="error")
                    reply = f"❌ **Analysis Failed:** {data['error']}"
                    diag = None
                else:
                    st.write("🌳 Parsing AST & building multi-level dependency graph...")
                    st.session_state.repo_data = data
                    st.session_state.repo_name = data["repo_name"]
                    st.session_state.file_nodes = data.get("file_level_nodes", [])

                    techs = ", ".join(data.get("tech_stack", [])) or "Standard stack"
                    entry_pts = ", ".join(data.get("entry_points", [])) or "Standard modules"

                    status.update(label="Repository Analyzed Successfully!", state="complete")
                    reply = (
                        f"✅ **Analyzed repository `{data['repo_name']}` successfully!**\n\n"
                        f"- 📁 **Files Parsed:** `{data['total_files_parsed']}` code files, `{data['total_sql_files']}` SQL schemas\n"
                        f"- 🛠️ **Tech Stack:** {techs}\n"
                        f"- 🚀 **Key Entry Points:** `{entry_pts}`\n\n"
                        f"**What would you like to know?** You can ask me:\n"
                        f"1. *'Explain the whole repo and how it works'* 📌\n"
                        f"2. *'Which directory does what?'* 📁\n"
                        f"3. *'How are files connected?'* 🔗\n"
                        f"4. *'What breaks if I change [function or file]?'* 💥"
                    )
                    diag = data.get("mermaid_diagram")

            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply, "diagram": diag})
            st.rerun()

        # Case B: Input is a Question or Chat Message
        else:
            with st.spinner("Analyzing codebase..."):
                try:
                    payload = {
                        "repo_name": st.session_state.repo_name,
                        "message": prompt_to_process
                    }
                    response = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=60)
                    resp_data = response.json()
                    reply = resp_data.get("answer", resp_data.get("error", "An error occurred."))
                    diag = resp_data.get("diagram")
                except requests.exceptions.RequestException as e:
                    reply = f"⚠️ Could not connect to backend server: {e}"
                    diag = None

            st.markdown(reply)
            if diag:
                with st.expander("📊 View Dependency Architecture Diagram", expanded=True):
                    st.code(diag, language="mermaid")

            st.session_state.messages.append({"role": "assistant", "content": reply, "diagram": diag})