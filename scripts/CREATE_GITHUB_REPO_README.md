# Create a private GitHub repository and push this project

This folder contains a PowerShell helper script `create_github_repo.ps1` that will create a private GitHub repository and push the current project to it.

Two methods are supported:

- Use GitHub CLI (`gh`) if you have it installed and authenticated. The script will call `gh repo create ... --private --push` for you.
- Use a Personal Access Token (PAT) if `gh` is not available. Provide a PAT with `repo` scope via the `GITHUB_TOKEN` environment variable or interactively when prompted.

Quick steps (recommended):

1. Open PowerShell in this project root (where `create_github_repo.ps1` resides).
2. Run the helper script:

```powershell
.\scripts\create_github_repo.ps1
```

Optional parameters:

-RepoName <name>    The repository name (defaults to current folder name)
-Description <text> A short description for the GitHub repo

Examples:

```powershell
.\scripts\create_github_repo.ps1 -RepoName "retace-main" -Description "Retace project imported from local machine"
```

Manual steps (if you prefer to do it yourself):

1. Initialize git and create a branch named `main` if needed:

```powershell
git init
git add --all
git commit -m "Initial import"
git branch -M main
```

2a. Using gh (recommended):

```powershell
gh repo create <owner>/<repo> --private --source=. --remote=origin --push --confirm
```

2b. Using Personal Access Token (PAT):

```powershell
$env:GITHUB_TOKEN = "<your-token-here>"
$payload = '{"name":"retace-main","private":true}'
$resp = Invoke-RestMethod -Method Post -Uri https://api.github.com/user/repos -Headers @{ Authorization = "token $env:GITHUB_TOKEN"; "User-Agent" = "powershell-create-repo" } -Body $payload -ContentType 'application/json'
git remote add origin $resp.clone_url
git push -u origin main
```

Security note: Keep your PAT secret. Prefer `gh auth login` or environment variables instead of embedding the token in scripts.
