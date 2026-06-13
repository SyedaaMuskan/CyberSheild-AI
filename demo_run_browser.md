Demo: Browser-based automated UI test (Playwright)

Prerequisites
- Ensure the React frontend app is running locally (default: `http://localhost:5173`).
  - To run: `cd frontend && npm install && npm run dev`
- Make sure the Python backend API is running: `python api.py`
- Install Python testing dependencies:

```bash
python -m pip install -r requirements.txt
python -m playwright install
```

Run the demo

```bash
python tests/browser_demo.py
```

What it does
- Opens the app in a Chromium browser.
- Submits three sample code snippets (safe, warning, malicious).
- Waits for the analysis results, captures screenshots to `demo_screenshots/`, and prints basic extracted metrics.

Notes
- If your Streamlit app runs on a different port, edit `base_url` in `tests/browser_demo.py`.
- Playwright will open a visible browser (not headless) so you can watch the demo.
