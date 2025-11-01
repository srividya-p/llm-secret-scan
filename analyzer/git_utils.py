import os
import re
import tempfile
import shutil

from git import Repo, GitCommandError, InvalidGitRepositoryError, NULL_TREE

tmpdir = None


def extract_added_lines(diff_text):
    added_lines = []
    hunk_re = re.compile(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")

    matches = list(hunk_re.finditer(diff_text))
    for i, h in enumerate(matches):
        new_start = int(h.group(1))

        body_start = h.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(diff_text)
        hunk_lines = diff_text[body_start:body_end].splitlines()

        current_new_line = new_start
        for line in hunk_lines:
            if line.strip() == r"\ No newline at end of file":
                continue

            if line.startswith("+"):
                if line.startswith("+++ "):
                    continue
                content = line[1:]
                if content:
                    added_lines.append(
                        {"content": content, "line_number": current_new_line}
                    )
                current_new_line += 1
            elif line.startswith("-"):
                continue
            else:
                current_new_line += 1

    return added_lines


def get_git_repo(repo_path_or_url):
    repo = None

    if repo_path_or_url.startswith(("http://", "https://", "git@")):
        tmpdir = tempfile.mkdtemp(prefix="git-scan-")
        print(f"[INFO] Cloning repo from {repo_path_or_url}...")
        repo = Repo.clone_from(repo_path_or_url, tmpdir)
    else:
        if not os.path.exists(repo_path_or_url):
            raise FileNotFoundError(f"Path does not exist: {repo_path_or_url}")
        repo = Repo(repo_path_or_url)
        if repo.bare:
            raise InvalidGitRepositoryError(
                f"Bare repo or not a valid Git repo: {repo_path_or_url}"
            )

    return repo


def collect_commits(repo_path_or_url, n):
    try:
        repo = get_git_repo(repo_path_or_url)
        commits = list(repo.iter_commits("HEAD", max_count=n))

        results = []
        for c in commits:
            diff = None
            parent = c.parents[0] if c.parents else None
            if parent:
                diff = parent.diff(c, create_patch=True)
            else:
                diff = c.diff(NULL_TREE, create_patch=True)

            changes = []
            for d in diff:
                # Skip binary or non-text diffs
                try:
                    diff_text = d.diff.decode("utf-8", errors="ignore")
                except Exception:
                    continue

                added_lines = extract_added_lines(diff_text)

                if not added_lines:
                    continue

                changes.append(
                    {"file": d.b_path or d.a_path, "added_lines": added_lines}
                )

            results.append(
                {"hash": c.hexsha[:7], "message": c.message.strip(), "changes": changes}
            )

        return results
    except (InvalidGitRepositoryError, GitCommandError) as e:
        print(f"[ERROR] Invalid or inaccessible repository: {e}")
        return []
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        return []
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return []
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)
