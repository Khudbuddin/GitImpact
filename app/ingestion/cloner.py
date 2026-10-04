import os
import shutil
from urllib.parse import urlparse
from git import Repo, GitCommandError

# Where all cloned repos will be temporarily stored
CLONE_BASE_DIR = os.path.normpath("data/cloned_repos")


def parse_repo_info(repo_url: str) -> dict:
    """Extracts owner, repo name, and sanitized folder name from a GitHub URL."""
    clean_url = repo_url.strip().rstrip("/")
    if clean_url.endswith(".git"):
        clean_url = clean_url[:-4]

    parsed = urlparse(clean_url)
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        raise ValueError("Invalid GitHub repository URL. Expected format: https://github.com/owner/repository")

    owner_name = parts[-2]
    repo_name = parts[-1]
    folder_name = f"{owner_name}_{repo_name}"

    return {
        "owner": owner_name,
        "repo": repo_name,
        "folder_name": folder_name,
        "clean_url": clean_url
    }


def clone_repository(repo_url: str) -> dict:
    """
    Clones a public GitHub repository to a local folder.

    Args:
        repo_url: The GitHub URL, e.g. https://github.com/user/repo or https://github.com/user/repo.git

    Returns:
        dict containing local_path, repo_name, owner, and folder_name.

    Raises:
        ValueError: if the URL is invalid or the repo cannot be cloned.
    """
    if "github.com" not in repo_url:
        raise ValueError("Please provide a valid GitHub URL (e.g. https://github.com/owner/repo)")

    info = parse_repo_info(repo_url)
    os.makedirs(CLONE_BASE_DIR, exist_ok=True)
    local_path = os.path.normpath(os.path.join(CLONE_BASE_DIR, info["folder_name"]))

    # If this repo was already cloned before, refresh it
    if os.path.exists(local_path):
        try:
            shutil.rmtree(local_path)
        except Exception:
            pass

    try:
        Repo.clone_from(repo_url, local_path, depth=1)  # shallow clone for speed
    except GitCommandError as e:
        raise ValueError(f"Failed to clone repository. It may be private or nonexistent. Details: {e}")

    # Standardize path with forward slashes for internal consistency
    normalized_path = local_path.replace("\\", "/")

    return {
        "local_path": normalized_path,
        "repo_name": info["repo"],
        "owner": info["owner"],
        "folder_name": info["folder_name"]
    }


if __name__ == "__main__":
    test_url = "https://github.com/octocat/Hello-World"
    result = clone_repository(test_url)
    print("Clone result:", result)