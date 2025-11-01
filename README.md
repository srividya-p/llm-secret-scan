# Secret Detection with LLMs

A small CLI tool that scans the latest commits of a Git repository for likely secret leaks using a combination of heuristics (regexes + entropy) and a Large Language Model verifier. The scanner does the following steps:
- clones or reads a Git repository (local path or remote URL)
- extracts added lines from recent commits
- pre-filters suspicious lines using regex patterns and Shannon entropy
- sends suspicious snippets to an LLM prompt to classify whether they contain secrets
- writes a JSON report of findings


## Requirements

The tool needs Python3, Git and optionally Pienv to run. One would also need a Google Generative AI API key. 

Install dependencies (pip):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Or using Pipenv:

```bash
pipenv shell
pipenv install
```


## Environment Variables

The scanner uses `google.generativeai` and `python-dotenv`. The library reads env vars on `genai.configure()`. Create a `.env` file at the project root with the following contents:

```
GOOGLE_API_KEY=ya29.your_google_api_key_here
```


## Usage

Basic command:

```bash
python scan.py -r <repo-path-or-url> -n 10 -o report.json
```

Options:
- `-r, --repo` : URL or local path to the Git repository (required)
- `-n, --n_commits` : number of commits to scan (default: 10)
- `-o, --out_file` : output JSON report file (default: `report.json`)

Example (scan last 5 commits of GitGuardian's sample secrets repo):

```bash
python scan.py -r https://github.com/GitGuardian/sample_secrets -n 5 -o report.json
```

Sample report entry (from `report.json`):

```json
{
    "snippet": "MONGO_URI = \"mongodb+srv:...\"",
    "line": 17,
    "file_path": "bucket_s3.py",
    "commit": "e9bf9aa",
    "type": "SECRET_LEAK",
    "secret_type": "MongoDB URI",
    "category": "DATABASE_SECRETS",
    "severity": "CRITICAL",
    "rationale": "The snippet contains a hardcoded MongoDB connection URI, which includes the username and password for database access. This credential allows direct access to the MongoDB instance, potentially leading to data compromise, unauthorized modification, or deletion.",
    "confidence": 1.0
    },
```


## Description of files

- Main entrypoint: `scan.py`
- Modules (in `analyzer/`):
	- `git_utils.py`: clone/read repo and collect recent commits + diffs
	- `heuristics.py`: prefilter suspicious lines using `patterns.json` and entropy threshold from `config.yaml`
	- `llm_client.py`: sends a prompt to an LLM (via `google.generativeai`) and validates the returned JSON
	- `report.py`: writes results to a JSON file
- Configuration: `config.yaml` (model, heuristics thresholds and prompt template)
- Regex patterns: `patterns.json` (Extracted from: https://gitlab.com/gitlab-org/security-products/secret-detection/secret-detection-rules/-/tree/main/rules/mit)


## Troubleshooting

- If `scan.py` prints `[ERROR] No commmits found!` ensure the repository path/URL is valid and has commits reachable from `HEAD`.
- If LLM responses are invalid JSON or missing fields, the client retries up to `llm.max_attempts` times (configured in `config.yaml`).
