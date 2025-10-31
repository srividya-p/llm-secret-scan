import json

from dotenv import load_dotenv
import google.generativeai as genai

from . import config

load_dotenv()

genai.configure()


TYPES = config.config["report"]["types"]
CATEGORIES = config.config["report"]["categories"]
SEVERITIES = config.config["report"]["severities"]
PROMPT_TEMPLATE = config.config["prompt_template"]
MODEL = config.config["llm"]["model"]
MAX_ATTEMPTS = config.config["llm"]["max_attempts"]


def validate_result(result):
    required_fields = {
        "type": TYPES,
        "secret_type": None,  # Can be any string
        "category": CATEGORIES,
        "severity": SEVERITIES,
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

    model = genai.GenerativeModel(MODEL)

    for attempt in range(MAX_ATTEMPTS):
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
