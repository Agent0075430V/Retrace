<#
.SYNOPSIS
    Create a private GitHub repository and push the current folder to it.

.DESCRIPTION
    This script helps you create a private repository on GitHub and push the current
    project to it. It tries to use the GitHub CLI (`gh`) if available; otherwise it
    falls back to using the GitHub REST API via a Personal Access Token (PAT).

    The script will:
      - check for git and initialize the repo if needed
      - create an initial commit (if there's not one)
      - create a private repo on GitHub
      - add the remote and push the `main` branch

    Notes:
      - You can set the environment variable GITHUB_TOKEN to a PAT with `repo` scope
        and the script will use it. If not set, you'll be prompted for a token.
      - If `gh` is installed and authenticated, the script will use it automatically.

.EXAMPLE
    PS> ./create_github_repo.ps1

#>

param(
    [string]$RepoName = "",
    [string]$Description = "Imported repository from local machine"
)

function Write-Log($msg){ Write-Host "[create-github-repo] $msg" }

# Determine working directory name if repo name not provided
if ([string]::IsNullOrWhiteSpace($RepoName)){
    $RepoName = Split-Path -Leaf (Get-Location)
}

Write-Log "Repository name: $RepoName"

# Sanity checks
if (-not (Get-Command git -ErrorAction SilentlyContinue)){
    Write-Error "git is not installed or not on PATH. Install git and re-run this script."; exit 1
}

$hasGh = (Get-Command gh -ErrorAction SilentlyContinue) -ne $null
if ($hasGh){ Write-Log "GitHub CLI detected. Will try to use 'gh' to create the repo." }
else { Write-Log "GitHub CLI not found. Will fall back to the REST API and require a PAT (GITHUB_TOKEN)." }

# Initialize git repo if needed
if (-not (Test-Path .git)){
    Write-Log "Initializing a new git repository..."
    git init
} else {
    Write-Log ".git directory already exists; skipping git init."
}

# Ensure there's at least one commit
$hasCommit = $false
try { git rev-parse --is-inside-work-tree > $null 2>&1 ; $hasCommit = (git rev-parse --verify HEAD > $null 2>&1; $LASTEXITCODE -eq 0) } catch { }

if (-not $hasCommit){
    Write-Log "Creating initial commit..."
    git add --all
    git commit -m "Initial import of $RepoName" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Log "No changes to commit or commit failed. Continuing..."
    }
}

# Use main as default branch
git branch -M main 2>$null

if ($hasGh){
    Write-Log "Running: gh repo create '$RepoName' --private --source=. --remote=origin --push --description '$Description' --confirm"
    $cmd = "gh repo create '$RepoName' --private --source=. --remote=origin --push --description '$Description' --confirm"
    try {
        iex $cmd
        Write-Log "Repository created and pushed using gh."
        exit 0
    } catch {
        Write-Warning "gh-based creation failed: $_. Falling back to REST API method."
    }
}

# REST API path (requires GITHUB_TOKEN env var or interactive prompt)
$token = $env:GITHUB_TOKEN
if (-not $token){
    Write-Host "A GitHub Personal Access Token (PAT) is required. Create one at https://github.com/settings/tokens with 'repo' scope."
    $sec = Read-Host -Prompt "Enter your GitHub Personal Access Token (it will not be stored)" -AsSecureString
    $token = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
}

if (-not $token){ Write-Error "No token provided. Aborting."; exit 1 }

# Create repository via API
$body = @{ name = $RepoName; description = $Description; private = $true } | ConvertTo-Json
Write-Log "Creating repository via GitHub API..."
try {
    $resp = Invoke-RestMethod -Method Post -Uri https://api.github.com/user/repos -Headers @{ Authorization = "token $token"; "User-Agent" = "powershell-create-repo" } -Body $body -ContentType 'application/json'
} catch {
    Write-Error "Failed to create repository via API. $_"; exit 1
}

$cloneUrl = $resp.clone_url
if (-not $cloneUrl){ Write-Error "Could not obtain clone_url from API response."; exit 1 }

Write-Log "Adding remote origin: $cloneUrl"
try { git remote remove origin 2>$null } catch { }
git remote add origin $cloneUrl

Write-Log "Pushing local main branch to remote..."
git push -u origin main
if ($LASTEXITCODE -ne 0){ Write-Warning "Push failed. Check credentials and remote URL. You can push manually: git push -u origin main" } else { Write-Log "Push complete." }

Write-Log "Done. Repository available at: $($resp.html_url)"
