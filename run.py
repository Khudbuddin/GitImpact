import sys
import time
import subprocess
import requests

def is_backend_alive():
    try:
        r = requests.get("http://127.0.0.1:8000/health", timeout=1)
        return r.status_code == 200
    except Exception:
        return False

def main():
    print("⚡ Starting GitImpact Platform...")

    backend_proc = None
    if not is_backend_alive():
        print("🚀 Launching FastAPI Backend on port 8000...")
        backend_proc = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "app.main:app",
            "--host", "0.0.0.0", "--port", "8000"
        ])
        # Wait up to 5s for backend to become alive
        for _ in range(10):
            time.sleep(0.5)
            if is_backend_alive():
                print("✅ FastAPI Backend is Online (http://127.0.0.1:8000)!")
                break
    else:
        print("✅ FastAPI Backend is already running on port 8000!")

    print("🎨 Launching Streamlit Studio on port 8501...")
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "frontend/app_ui.py",
            "--server.address", "0.0.0.0",
            "--server.port", "8501",
            "--server.headless", "true"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Stopping GitImpact...")
    finally:
        if backend_proc:
            backend_proc.terminate()
            print("🛑 FastAPI Backend stopped.")

if __name__ == "__main__":
    main()
