# ⚡ GitImpact

> **AI-Powered Codebase Intelligence & Change Blast-Radius Analysis Platform**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B.svg?style=flat&logo=Streamlit&logoColor=white)](https://streamlit.io)
[![Tree-Sitter](https://img.shields.io/badge/Tree--Sitter-AST%20Parsing-22c55e.svg?style=flat)](https://tree-sitter.github.io)
[![NetworkX](https://img.shields.io/badge/NetworkX-Graph%20Traversal-blue.svg?style=flat)](https://networkx.org)
[![Groq](https://img.shields.io/badge/Groq-Llama%203.3%20Inference-f97316.svg?style=flat)](https://groq.com)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 📌 Overview

**GitImpact** is an intelligent developer platform that answers the crucial engineering question:
> *"If I modify this function or refactor this file, what other parts of the codebase will break?"*

Instead of relying on fragile text searches or regex matching, **GitImpact** ingests any public GitHub repository, constructs concrete **Abstract Syntax Tree (AST)** representations using `tree-sitter`, models the code into a multi-level **Directed Dependency Graph** via `NetworkX`, and leverages **Groq-accelerated LLM Agents** to provide deep architectural insights and change impact analysis in plain English.

---

## ✨ Key Features

- 💬 **Natural Conversational Flow**: Start chatting casually, ask general questions, or paste a repository URL at any time.
- 🌳 **True AST Parsing**: Extracts functions, classes, imports, and calls with scope-tracking using `tree-sitter` (Python & Java) and `sqlparse` (SQL schemas).
- 🕸️ **Multi-Level Dependency Graph**: Tracks file containment (`contains`), function invocations (`calls`), and module imports (`imports`).
- 💥 **Change Blast-Radius Engine**: Reverse Breadth-First Search (BFS) graph traversal calculates exact topological distances for all downstream affected components.
- 🧠 **Multi-Intent AI Orchestrator**: Automatically routes questions to specialized agents:
  - **Whole Repository Overview**: Explains the core purpose, tech stack, and workflow.
  - **Directory Mapping**: Explains the exact responsibility of every directory.
  - **File Connections & Flow**: Analyzes dependencies and renders an interactive **Mermaid flowchart**.
  - **Specific Code Drilldown**: Explains specific functions or files.
  - **Blast-Radius Impact Analysis**: Evaluates risk and suggests testing checklists before deploying code changes.
- 📏 **Adaptive Response Length**: Automatically scales depth from quick 2-bullet TL;DRs to in-depth, step-by-step architectural walkthroughs.
- 🎨 **Modern Streamlit Dashboard**: Includes an active repository summary card, tech stack badges, an interactive directory explorer, and one-click quick prompt chips.

---

## 🏗️ Architecture & Data Flow

```mermaid
flowchart TD
    User([Developer / User]) <--> UI[Streamlit UI\nfrontend/app_ui.py]
    UI <--> API[FastAPI Gateway\napp/api/routes.py]

    subgraph Ingestion & AST Analysis
        API --> Cloner[Git Ingestion\napp/ingestion/cloner.py]
        Cloner --> Scanner[Repository Scanner\napp/parsing/repo_scanner.py]
        Scanner --> PyParser[Python AST\ntree-sitter-python]
        Scanner --> JavaParser[Java AST\ntree-sitter-java]
        Scanner --> SqlParser[SQL DDL\nsqlparse]
    end

    subgraph Graph Engine
        PyParser & JavaParser & SqlParser --> Builder[Dependency Graph Builder\napp/graph/builder.py]
        Builder --> Graph[(NetworkX DiGraph)]
        Graph --> Traversal[Reverse BFS Traversal\napp/graph/traversal.py]
    end

    subgraph Multi-Agent AI System
        API --> Router[Intent Orchestrator\napp/agents/orchestrator.py]
        Router -->|Overview / Architecture| Explainer[Explainer Agent\napp/agents/explainer_agent.py]
        Router -->|Impact / Risk| ImpactAgent[Impact Agent\napp/agents/impact_agent.py]
        Traversal --> ImpactAgent
        Explainer & ImpactAgent --> Groq[Groq Llama-3.3 LLM]
    end

    subgraph Persistence
        Scanner --> DB[(SQLite Cache\napp/database/db.py)]
    end
```

---

## 📂 Project Structure

```plaintext
GitImpact/
├── app/
│   ├── main.py                     # FastAPI entry point
│   ├── agents/
│   │   ├── orchestrator.py         # Multi-intent routing & adaptive length engine
│   │   ├── explainer_agent.py      # Architecture, repo, & file explainer agent
│   │   └── impact_agent.py         # Change blast-radius & risk assessment agent
│   ├── api/
│   │   └── routes.py               # REST API endpoints (/clone, /chat, /ask, /health)
│   ├── database/
│   │   └── db.py                   # SQLite persistence & metadata caching
│   ├── graph/
│   │   ├── builder.py              # AST dependency graph builder & Mermaid generator
│   │   └── traversal.py            # Reverse BFS topological distance traversal
│   ├── ingestion/
│   │   └── cloner.py               # Shallow Git repository cloner & path sanitizer
│   └── parsing/
│       ├── repo_scanner.py         # Directory mapper, tech stack detector, & README parser
│       ├── python_parser.py        # Tree-sitter AST parser for Python
│       ├── java_parser.py          # Tree-sitter AST parser for Java
│       └── sql_parser.py           # SQL DDL schema parser
├── frontend/
│   └── app_ui.py                   # Streamlit dashboard & interactive chat workspace
├── data/                           # Cloned repositories & SQLite database cache
├── .env.example                    # Template for environment variables
├── .gitignore                      # Git exclusion rules
├── requirements.txt                # Pinned production dependencies
└── README.md                       # Complete documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+** (tested with Python 3.10 – 3.13)
- **Git** installed and available in your system path
- A free **Groq API Key** (get one at [console.groq.com](https://console.groq.com))

---

### 2. Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Khudbuddin/GitImpact.git
   cd GitImpact
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Copy the example `.env` file and insert your Groq API key:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and set your key:
   ```env
   GROQ_API_KEY=gsk_your_groq_api_key_here
   GROQ_MODEL=llama-3.3-70b-versatile
   ```

---

### 3. Running GitImpact

You will need **two terminal windows**: one for the backend API and one for the frontend UI.

#### Terminal 1 — Start the FastAPI Backend:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
*The API will be live at `http://127.0.0.1:8000`. You can visit `http://127.0.0.1:8000/docs` for interactive Swagger documentation.*

#### Terminal 2 — Start the Streamlit Frontend:
```bash
streamlit run frontend/app_ui.py
```
*The web interface will open automatically in your browser at `http://localhost:8501`.*

---

## 💡 Example Queries to Try

Once you paste a repository URL (e.g. `https://github.com/Khudbuddin/Smart-Expense-Categorizer`), you can ask anything:

| Query Type | Example Prompt |
| :--- | :--- |
| **High-Level Overview** | *"Explain the whole repo and its purpose"* |
| **Directory Map** | *"Which directory does what? Explain the folder structure."* |
| **Architecture & Flow** | *"How are files connected and what is the data flow?"* |
| **Main Entry Points** | *"What are the entry point files and how does execution start?"* |
| **Specific Code** | *"What does the `classify_intent` function do in `orchestrator.py`?"* |
| **Change Impact** | *"What will break if I change `clone_repository`?"* |
| **Concise Summary** | *"Briefly summarize what this project does in 2 bullets"* |
| **Deep Dive** | *"Walk me through the entire architecture step by step in detail"* |

---

## 🛡️ License

This project is licensed under the **MIT License**.
