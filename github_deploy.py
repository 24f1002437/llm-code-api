# github_deploy.py
import os
import shutil
import requests
from git import Repo, GitCommandError
from config import GITHUB_USERNAME, GITHUB_TOKEN

def deploy_to_github(local_dir: str, repo_name: str, token: str):
    """
    Pushes generated app to GitHub and returns repo URLs.
    """
    repo_url = f"https://{GITHUB_USERNAME}:{token}@github.com/{GITHUB_USERNAME}/{repo_name}.git"
    pages_url = f"https://{GITHUB_USERNAME}.github.io/{repo_name}/"

    # Ensure GitHub repo exists
    create_github_repo(repo_name)

    # Clone repo into temp folder
    clone_dir = f"temp/{repo_name}_repo"
    if os.path.exists(clone_dir):
        shutil.rmtree(clone_dir)
    repo = Repo.clone_from(repo_url, clone_dir)

    # Copy generated files
    for item in os.listdir(local_dir):
        src = os.path.join(local_dir, item)
        dst = os.path.join(clone_dir, item)
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    # Commit and push
    try:
        repo.git.add(A=True)
        repo.index.commit("Update generated app")
        repo.git.push("--set-upstream", "origin", repo.active_branch.name)
    except GitCommandError as e:
        print(f"[ERROR] Git push failed: {e}")
        raise

    commit_sha = repo.head.commit.hexsha
    print(f"[INFO] Deployed {repo_name} to GitHub at commit {commit_sha}")
    return repo_url, commit_sha, pages_url
