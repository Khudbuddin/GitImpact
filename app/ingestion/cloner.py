import os
import shutil
from git import Repo, GitCommandError

# Where all cloned repos will be temporarily stored
CLONE_BASE_DIR = "data/cloned_repos"


def clone_repository(repo_url: str) -> str:
    """
    Clones a public GitHub repository to a local folder.

    Args:
        repo_url: The GitHub URL, e.g. https://github.com/user/repo.git

    Returns:
        The local path where the repo was cloned.

    Raises:
        ValueError: if the URL is invalid or the repo can't be cloned.
    """
    if not repo_url.startswith("https://github.com/"):
        raise ValueError("Please provide a valid GitHub URL (must start with https://github.com/)")

    # Extract a folder name from the URL, e.g. "user_repo"
    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    owner_name = repo_url.rstrip("/").split("/")[-2]
    folder_name = f"{owner_name}_{repo_name}"

    local_path = os.path.join(CLONE_BASE_DIR, folder_name)

    # If this repo was already cloned before, remove the old copy first
    if os.path.exists(local_path):
        shutil.rmtree(local_path)

    try:
        Repo.clone_from(repo_url, local_path)
    except GitCommandError as e:
        raise ValueError(f"Failed to clone repository. It may be private or the URL is wrong. Details: {e}")

    return local_path


# Quick manual test — only runs if you execute this file directly
if __name__ == "__main__":
    test_url = "https://github.com/octocat/Hello-World.git"
    path = clone_repository(test_url)
    print(f"Repository cloned successfully to: {path}")