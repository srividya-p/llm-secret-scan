import json

import google.generativeai as genai
from dotenv import load_dotenv

from .finding_types import FindingType

load_dotenv()

genai.configure()

PROMPT_TEMPLATE = """
You are a security auditor reviewing Git diffs.
Determine if the following snippet likely leaks secrets or sensitive data.
Return JSON with the following keys:
- type: Must be one of ["SECRET_LEAK", "INFORMATION_DISCLOSURE", "NO_LEAK"]
- rationale: Your explanation for the classification
- confidence: A number between 0 and 1

Commit message: {commit_msg}
File: {file_path}
Snippet: {diff_snippet}
"""


def analyze_with_llm(diff_snippet, commit_msg, file_path):
    prompt = PROMPT_TEMPLATE.format(
        diff_snippet=diff_snippet, commit_msg=commit_msg, file_path=file_path
    )

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    text = response.text.strip()

    if text.startswith("```json"):
        text = text.replace("```json", "", 1)
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        result = json.loads(text)
        finding_type = FindingType.from_string(result.get("type", ""))
        if finding_type != FindingType.NO_LEAK:
            result["type"] = finding_type.to_dict()
            return result
        return None
    except Exception:
        return {
            "type": FindingType.UNKNOWN.to_dict(),
            "rationale": text,
            "confidence": 0.5,
        }
