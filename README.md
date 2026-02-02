# Student Group Matchmaking

Form student groups based on schedule overlaps (exact time-slot matching). Built with Streamlit and pandas.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Or use the launcher: `python main.py`

## Deploy on Streamlit Community Cloud

1. **Put your code on GitHub**
   - Create a new repository on [github.com](https://github.com/new) (e.g. `student-group-matchmaking`).
   - Do **not** initialize with a README if you’re pushing this folder (you already have one).
   - In your project folder, run:

   ```bash
   git init
   git add app.py main.py requirements.txt README.md
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git push -u origin main
   ```

   Replace `YOUR_USERNAME` and `YOUR_REPO_NAME` with your GitHub username and repository name.

2. **Deploy on Streamlit Community Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
   - Click **“New app”**.
   - Choose your GitHub **repository**, **branch** (e.g. `main`), and set **Main file path** to `app.py`.
   - Click **“Deploy!”**. Streamlit will use `requirements.txt` and run `streamlit run app.py`.

Your app will be live at a URL like `https://YOUR_APP_NAME.streamlit.app`.
