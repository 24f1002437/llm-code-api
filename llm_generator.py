import os
import base64
import google.generativeai as genai  #  Correct Gemini SDK
from config import GEMINI_API_KEY


def generate_app(brief: str, attachments: list, output_dir: str, use_mock: bool = False):
    """
    Generates a minimal HTML/CSS/JS app using Gemini API first, fallback to mock.
    """
    os.makedirs(output_dir, exist_ok=True)

    # ----------------------------
    # SAVE ATTACHMENTS LOCALLY
    # ----------------------------
    for att in attachments:
        att_name = att.get("name")
        att_url = att.get("url", "")
        if not att_name or not att_url:
            print(f"[WARN] Skipping invalid attachment: {att}")
            continue
        att_path = os.path.join(output_dir, att_name)
        if att_url.startswith("data:"):
            header, encoded = att_url.split(",", 1)
            with open(att_path, "wb") as f:
                f.write(base64.b64decode(encoded))
        else:
            print(f"[WARN] Attachment {att_name} does not have a valid data URI.")

    # ----------------------------
    # TRY GEMINI API FIRST
    # ----------------------------
    if not use_mock and GEMINI_API_KEY:
        try:
            print("[TASK] Generating app using Gemini API...")
            genai.configure(api_key=GEMINI_API_KEY)

            model = genai.GenerativeModel("gemini-1.5-flash")

            attachment_info = "\n".join([
                f"{att.get('name','?')}: {att.get('url','')[:50]}..." for att in attachments
            ])
            prompt = f"""
You are an expert web developer.
Generate a minimal working HTML/CSS/JS app based on this brief:
{brief}

Attachments info:
{attachment_info}

Provide:
- index.html
- README.md
- MIT LICENSE
Each file should be clearly marked using ### FILE: filename
"""

            response = model.generate_content(prompt)
            code_text = response.text or ""

            # Save raw output for debugging
            with open(os.path.join(output_dir, "gemini_raw.txt"), "w", encoding="utf-8") as f:
                f.write(code_text)

            # ----------------------------
            # PARSE FILES FROM LLM OUTPUT
            # ----------------------------
            files = {"index.html": "", "README.md": "", "LICENSE": ""}
            current_file = None
            for line in code_text.splitlines():
                line = line.strip()
                if line.startswith("### FILE:"):
                    fname = line.split(":", 1)[1].strip()
                    current_file = fname if fname in files else None
                    continue
                if current_file:
                    files[current_file] += line + "\n"

            # Write files
            for fname, content in files.items():
                file_path = os.path.join(output_dir, fname)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content.strip() or f"<!-- {fname} generated -->")

            print(f"[Gemini ] App generated successfully in: {output_dir}")
            return output_dir

        except Exception as e:
            print(f"[ERROR] Gemini API failed: {e}\nFalling back to mock mode.")
            use_mock = True

    # ----------------------------
    # MOCK MODE (fallback)
    # ----------------------------
    print("[MOCK] Generating fallback app...")
    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write("<!DOCTYPE html><html><body><h1>Hello World</h1></body></html>")
    with open(os.path.join(output_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write("# App\nGenerated locally without API.")
    with open(os.path.join(output_dir, "LICENSE"), "w", encoding="utf-8") as f:
        f.write("MIT License")
    print(f"[MOCK] App generated in {output_dir}")
    return output_dir
