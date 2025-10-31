import re
import math

PATTERNS = {
    "AWS Access Key": r"AKIA[0-9A-Z]{16}",
    "Private Key": r"-----BEGIN (?:RSA|DSA|EC|PGP) PRIVATE KEY-----",
    "API Token": r"api[_-]?key\s*=\s*['\"]?[A-Za-z0-9_\-]{16,}['\"]?",
    "Password": r"pass(word)?\s*=\s*['\"].+['\"]",
}


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
            or shannon_entropy(line) > 4.5
        )

        if is_suspect:
            suspects.append({"snippet": line.rstrip(), "line": i + 1})
            seen_snippets.add(line)

    return suspects
