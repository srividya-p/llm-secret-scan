import re
import math

from . import config

PATTERNS = {k: re.compile(v) for k, v in config.patterns.items()}
ENTROPY_THRESHOLD = config.config["heuristics"]["entropy_threshold"]


def shannon_entropy(s):
    if not s:
        return 0
    probs = [float(s.count(c)) / len(s) for c in set(s)]
    return -sum(p * math.log(p, 2) for p in probs)


def prefilter_suspects(lines):
    suspects = []
    seen_snippets = set()

    for i, line in enumerate(lines):
        if line in seen_snippets:
            continue

        is_suspect = (
            any(re.search(regex, line) for regex in PATTERNS.values())
            or shannon_entropy(line) > ENTROPY_THRESHOLD
        )

        if is_suspect:
            suspects.append({"snippet": line.rstrip(), "line": i + 1})
            seen_snippets.add(line)

    return suspects
