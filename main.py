import os
import sys
import time
import webbrowser
import subprocess


def main():
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(script_dir, "app.py")

    if not os.path.isfile(app_path):
        print(f"Error: app.py not found in {script_dir}")
        sys.exit(1)

    # Streamlit's default URL
    url = "http://localhost:8501"

    print("Starting Streamlit...")
    print("The app will open in your browser shortly.")
    print("To stop the app: close this window or press Ctrl+C.")
    print()

    # Start Streamlit
    process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", app_path, "--server.headless", "false"],
        cwd=script_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    time.sleep(2)
    webbrowser.open(url)

    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
        process.wait()
        print("\nStopped.")


if __name__ == "__main__":
    main()
