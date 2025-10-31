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
    for i, line in enumerate(lines):
        for name, regex in PATTERNS.items():
            if re.search(regex, line):
                suspects.append({"snippet": line, "type": name, "line": i + 1})
                break
        if shannon_entropy(line) > 4.5:
            suspects.append({"snippet": line, "type": "High Entropy", "line": i + 1})
    return suspects
