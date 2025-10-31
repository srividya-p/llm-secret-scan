import os
import tempfile
import shutil

from git import Repo, GitCommandError, InvalidGitRepositoryError

tmpdir = None


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
            parent = c.parents[0] if c.parents else None
            diff = c.diff(parent, create_patch=True)
            changes = []
            for d in diff:
                # Skip binary or non-text diffs
                try:
                    diff_text = d.diff.decode("utf-8", errors="ignore")
                except Exception:
                    continue

                added_lines = [
                    line[1:].rstrip()
                    for line in diff_text.splitlines()
                    if line.startswith("+") and not line.startswith("+++")
                ]
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
