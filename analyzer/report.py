import json


def write_report(findings, out_file):
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(findings, f, indent=4, ensure_ascii=False)
    print(f"[+] Report written to {out_file}")
