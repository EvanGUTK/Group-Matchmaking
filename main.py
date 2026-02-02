"""
Launcher for the Student Group Matchmaking app.
Run this file to start Streamlit and open the app in your browser.

  py main.py

Or double-click main.py (if .py is associated with Python).
"""

import os
import sys
import time
import webbrowser
import subprocess


def main():
    # Run from the folder containing app.py so paths and cwd are correct
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(script_dir, "app.py")

    if not os.path.isfile(app_path):
        print(f"Error: app.py not found in {script_dir}")
        sys.exit(1)

    # Streamlit's default URL (use --server.port in the command if you change it)
    url = "http://localhost:8501"

    print("Starting Streamlit...")
    print("The app will open in your browser shortly.")
    print("To stop the app: close this window or press Ctrl+C.")
    print()

    # Start Streamlit in a subprocess (same Python as this script)
    process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", app_path, "--server.headless", "false"],
        cwd=script_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # Give the server a moment to start, then open the browser
    time.sleep(2)
    webbrowser.open(url)

    # Keep this script running until Streamlit exits
    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
        process.wait()
        print("\nStopped.")


if __name__ == "__main__":
    main()
