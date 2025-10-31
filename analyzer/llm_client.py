import json

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure()

PROMPT_TEMPLATE = """
You are a security auditor reviewing Git diffs.
Determine if the following snippet likely leaks secrets or sensitive data.
Return JSON with the following keys:
- type: Must be one of ["SECRET_LEAK", "INFORMATION_DISCLOSURE", "NO_LEAK"]
- secret_type: Identify the specific type of secret (e.g. "AWS Key", "OAuth Token", "SSH Key", "API Key", "Database Password", etc.)
- category: Must be one of ["CLOUD_CREDENTIALS", "AUTH_TOKENS", "ENCRYPTION_KEYS", "DATABASE_SECRETS", "SERVICE_CREDENTIALS", "OTHER"]
- severity: Must be one of ["CRITICAL", "HIGH", "MEDIUM", "LOW"] based on the potential impact
- rationale: Your brief explanation for why this type of secret is sensitive
- confidence: A number between 0 and 1

Commit message: {commit_msg}
File: {file_path}
Snippet: {diff_snippet}

Consider the context of the file path and commit message when determining the secret type.
"""


def validate_result(result):
    valid_types = ["SECRET_LEAK", "INFORMATION_DISCLOSURE", "NO_LEAK"]
    valid_categories = [
        "CLOUD_CREDENTIALS",
        "AUTH_TOKENS",
        "ENCRYPTION_KEYS",
        "DATABASE_SECRETS",
        "SERVICE_CREDENTIALS",
        "OTHER",
    ]
    valid_severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

    required_fields = {
        "type": valid_types,
        "secret_type": None,  # Can be any string
        "category": valid_categories,
        "severity": valid_severities,
        "rationale": None,  # Can be any string
        "confidence": lambda x: isinstance(x, (int, float)) and 0 <= x <= 1,
    }

    for field, valid_values in required_fields.items():
        if field not in result:
            return False, f"Missing required field: {field}"

        if valid_values:
            if callable(valid_values):
                if not valid_values(result[field]):
                    return False, f"Invalid value for {field}: {result[field]}"
            elif result[field] not in valid_values:
                return False, f"Invalid value for {field}: {result[field]}"

    return True, None


def analyze_with_llm(diff_snippet, commit_msg, file_path):
    prompt = PROMPT_TEMPLATE.format(
        diff_snippet=diff_snippet, commit_msg=commit_msg, file_path=file_path
    )

    model = genai.GenerativeModel("gemini-2.5-flash")

    for attempt in range(2):
        response = model.generate_content(prompt)
        text = response.text.strip()

        if text.startswith("```json"):
            text = text.replace("```json", "", 1)
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

        try:
            result = json.loads(text)
            if result.get("type") == "NO_LEAK":
                return None

            is_valid, error = validate_result(result)
            if is_valid:
                return result

            if attempt == 0:
                prompt += f"\n\nPrevious response had an error: {error}. Please provide a valid response."

        except json.JSONDecodeError:
            if attempt == 0:
                prompt += "\n\nPrevious response was not valid JSON. Please provide a properly formatted JSON response."

    # Both attempts failed
    return None
