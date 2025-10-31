import argparse

from tqdm import tqdm

from analyzer.git_utils import collect_commits
from analyzer.heuristics import prefilter_suspects
from analyzer.llm_client import analyze_with_llm
from analyzer.report import write_report


def main():
    parser = argparse.ArgumentParser(
        description="CLI tool to find secrets in GIT repos using LLMs"
    )
    parser.add_argument(
        "-r", "--repo", help="URL or path to GIT repository", required=True
    )
    parser.add_argument(
        "-n",
        "--n_commits",
        help="Number of commits to scan",
        type=int,
        default=10,
    )
    parser.add_argument(
        "-o",
        "--out_file",
        help="Name of file to store results in",
        default="report.json",
    )
    args = parser.parse_args()

    commits = collect_commits(args.repo, args.n_commits)
    if not commits:
        print("[ERROR] No commmits found!")
        exit(1)

    findings = []
    for commit in tqdm(commits, desc="Scanning commits", unit="commit"):
        all_suspects = []
        for change in commit["changes"]:
            suspects = prefilter_suspects(change["added_lines"])
            if suspects:
                for s in suspects:
                    s["file_path"] = change["file"]
                all_suspects.extend([(s, change["file"]) for s in suspects])

        if all_suspects:
            for suspect, file_path in tqdm(
                all_suspects,
                desc=f"Analyzing suspects in {commit['hash'][:7]}",
                leave=False,
                unit="suspect",
            ):
                result = analyze_with_llm(
                    diff_snippet=suspect["snippet"],
                    commit_msg=commit["message"],
                    file_path=file_path,
                )
                if result:
                    findings.append({**suspect, "commit": commit["hash"], **result})

    write_report(findings, args.out_file)


if __name__ == "__main__":
    main()
