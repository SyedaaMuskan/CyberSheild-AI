from playwright.sync_api import sync_playwright
import time
import re
import os

SAMPLES = [
    ("Safe code", "def append_user_data(username, database):\n    return True"),
    ("Warning code", "return getattr(ConfigClass, setting_name, None)"),
    ("Malicious code", "import importlib\nreturn eval(payload_str)")
]

def dump_metrics(text: str):
    score_match = re.search(r"Risk Score\n*(\d{1,3})", text)
    verdict_match = re.search(r"Verdict\n*([A-Z_]+|SAFE|WARN|BLOCK)", text)
    return score_match.group(1) if score_match else None, (verdict_match.group(1) if verdict_match else None)


def run_demo(base_url="http://localhost:5173"):
    screenshots_dir = "demo_screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        try:
            page.goto(base_url)
        except Exception:
            print("Failed to reach React frontend. Is `npm run dev` running in the frontend folder?")
            return
        
        page.wait_for_timeout(1000)

        for idx, (name, code) in enumerate(SAMPLES, start=1):
            print(f"--- Testing: {name}")

            # Fill the main code text area
            page.locator("textarea").first.fill(code)

            # Click the analysis button
            page.get_by_role("button", name="Analyze Risk").click()

            # Wait for results area to appear
            page.wait_for_selector("text=Reasoning", timeout=15000)

            # Snapshot and dump page text
            out_path = os.path.join(screenshots_dir, f"result_{idx}.png")
            page.screenshot(path=out_path, full_page=True)
            body_text = page.inner_text("body")
            score, verdict = dump_metrics(body_text)
            print(f"Screenshot saved to: {out_path}")
            print("Extracted -> Risk Score:", score, "Verdict:", verdict)

            # Click the PR button to take a screenshot of the modal
            if page.locator("text=Export to GitHub PR").count() > 0:
                page.get_by_text("Export to GitHub PR").click()
                page.wait_for_timeout(500)
                pr_out_path = os.path.join(screenshots_dir, f"result_{idx}_pr_modal.png")
                page.screenshot(path=pr_out_path, full_page=True)
                print(f"PR Modal Screenshot saved to: {pr_out_path}")
                # Close modal
                page.get_by_role("button", name="Close").click()
                page.wait_for_timeout(500)

            time.sleep(1)

        browser.close()


if __name__ == "__main__":
    run_demo()
