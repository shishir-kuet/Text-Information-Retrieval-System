# Git Setup Instructions

Follow these steps to initialize Git and push to GitHub.

## Step 1: Initialize Git Locally

Open terminal in VS Code (Ctrl + `) and run:

```bash
git init
git add .
git commit -m "chore: initialize project structure and documentation"
```

## Step 2: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `digital-book-source-retrieval` (or your preferred name)
3. Description: "Indexed Search Engine for Controlled Digital Library"
4. Choose **Public** or **Private** (as required by your instructor)
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

## Step 3: Connect to GitHub

Copy the repository URL from GitHub, then run:

```bash
git remote add origin <YOUR_REPO_URL>
git branch -M main
git push -u origin main
```

Example:

```bash
git remote add origin https://github.com/yourusername/digital-book-source-retrieval.git
git branch -M main
git push -u origin main
```

## Step 4: Create develop Branch

```bash
git checkout -b develop
git push -u origin develop
```

## Step 5: Set Branch Protection Rules

Go to GitHub repository settings:

1. Click **Settings** → **Branches**
2. Click **Add branch protection rule**
3. Branch name pattern: `main`
4. Enable:
   - ✅ Require a pull request before merging
   - ✅ Require approvals: 1
5. Click **Create**

## Step 6: Add Team Member as Collaborator

1. Go to repository **Settings** → **Collaborators**
2. Click **Add people**
3. Enter teammate's GitHub username
4. They will receive an invitation

## Step 7: Verify Setup

Check that you have:

- ✅ `main` branch (protected)
- ✅ `develop` branch
- ✅ All files committed
- ✅ Teammate added as collaborator
- ✅ Branch protection enabled

## Step 8: Create First Feature Branch

Now you're ready for development:

```bash
git checkout develop
git pull
git checkout -b feature/backend-bootstrap
```

Start working on backend setup!

---

## Quick Reference

### Common Git Commands

```bash
# Check current branch and status
git status
git branch

# Switch branches
git checkout develop
git checkout -b feature/new-feature

# Stage and commit
git add .
git commit -m "feat: description"

# Push to GitHub
git push
git push -u origin feature-name  # First time for new branch

# Update from remote
git pull

# View commit history
git log --oneline --graph
```

### Before Starting Any Work

```bash
git checkout develop
git pull
git checkout -b feature/descriptive-name
```

### After Completing Work

```bash
git add .
git commit -m "type: description"
git push -u origin feature/descriptive-name
```

Then create Pull Request on GitHub!
