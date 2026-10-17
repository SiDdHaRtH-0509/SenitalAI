# Push this repository to GitHub

1. Extract the ZIP. The extracted folder is the repository root (`sentinel-ai/`).
2. Create an empty GitHub repository named `sentinel-ai` (do not initialize it with another README/license, because this folder already has files).
3. Open a terminal in the extracted folder and run:

```bash
git init
git branch -M main
git add .
git status
# Inspect the staged files; make sure no secrets or private data are present.
git commit -m "Initialize SentinelAI datathon repository"
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with the URL shown by GitHub. Do not put a token or password into the URL.

## Add leads
After the first push, invite all four leads as collaborators. Each lead should clone the repository, create their assigned branch listed in `TEAM_ROLES.md`, and submit changes via pull requests. Protect `main` from direct pushes if the GitHub plan/settings allow it.

This ZIP intentionally does not include a `.git` directory because it cannot know your GitHub remote. It is structured to initialize cleanly as a Git repository.
