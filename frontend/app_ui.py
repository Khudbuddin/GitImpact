import streamlit as st
import requests

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="GitImpact", layout="centered")
st.title("GitImpact")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Paste a public GitHub repo link to get started."}
    ]
if "repo_name" not in st.session_state:
    st.session_state.repo_name = None
if "file_nodes" not in st.session_state:
    st.session_state.file_nodes = []
if "pending_file_question" not in st.session_state:
    st.session_state.pending_file_question = None

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("Type a message...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        # Step 1: no repo cloned yet — treat input as a repo URL
        if st.session_state.repo_name is None:
            with st.spinner("Cloning and analyzing repository..."):
                response = requests.post(f"{BACKEND_URL}/clone", json={"repo_url": user_input})
                data = response.json()

            if "error" in data:
                reply = f"Couldn't clone that repo: {data['error']}"
            else:
                st.session_state.repo_name = data["repo_name"]
                st.session_state.file_nodes = data["file_level_nodes"]
                reply = (f"Analyzed **{data['repo_name']}** — {data['total_files_parsed']} code files found. "
                         f"What would you like to know? You can ask about a specific file or function, "
                         f"or just describe what you're curious about.")
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

        else:
            # Step 2: try to detect which file the user means
            detected_file = None
            for f in st.session_state.file_nodes:
                filename = f.split("/")[-1]
                if filename.lower() in user_input.lower():
                    detected_file = f
                    break

            # If we were waiting for a file clarification from the previous turn
            if not detected_file and st.session_state.pending_file_question:
                for f in st.session_state.file_nodes:
                    if f.split("/")[-1].lower() in user_input.lower():
                        detected_file = f
                        break
                question_to_ask = st.session_state.pending_file_question
                st.session_state.pending_file_question = None
            else:
                question_to_ask = user_input

            if not detected_file:
                reply = ("I'm not sure which file you mean — could you mention the file name? "
                          f"For example: {', '.join(f.split('/')[-1] for f in st.session_state.file_nodes[:5])}...")
                st.session_state.pending_file_question = user_input
            else:
                with st.spinner("Thinking..."):
                    response = requests.post(f"{BACKEND_URL}/chat", json={
                        "repo_name": st.session_state.repo_name,
                        "message": question_to_ask,
                        "file_path": detected_file
                    })
                    data = response.json()
                reply = data.get("answer", data.get("error", "Something went wrong."))

            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})