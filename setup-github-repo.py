#!/usr/bin/env python3
"""
GitHub Repository Setup Script for Visey Recommender
Initializes Git repository and prepares for GitHub upload
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout.strip())
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return None

def check_git_installed():
    """Check if Git is installed."""
    result = run_command("git --version", check=False)
    return result is not None and result.returncode == 0

def initialize_git_repo():
    """Initialize Git repository and make initial commit."""
    print("🔧 Initializing Git repository...")
    
    # Initialize repo
    run_command("git init")
    
    # Add all files
    run_command("git add .")
    
    # Make initial commit
    run_command('git commit -m "feat: initial commit - Visey Recommender System v1.0.0"')
    
    print("✅ Git repository initialized with initial commit")

def create_gitignore_additions():
    """Add any missing entries to .gitignore."""
    gitignore_path = Path(".gitignore")
    
    additional_entries = [
        "# Visey Recommender specific",
        "*.log",
        ".pytest_cache/",
        "htmlcov/",
        ".coverage",
        "instance/",
        ".env.local",
        "data/cache.db*",
        "data/feedback.db*"
    ]
    
    if gitignore_path.exists():
        current_content = gitignore_path.read_text()
        new_entries = []
        
        for entry in additional_entries:
            if entry not in current_content:
                new_entries.append(entry)
        
        if new_entries:
            with open(gitignore_path, "a") as f:
                f.write("\n" + "\n".join(new_entries) + "\n")
            print("✅ Updated .gitignore with additional entries")

def setup_pre_commit():
    """Set up pre-commit hooks."""
    pre_commit_config = """
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
  
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203]
"""
    
    with open(".pre-commit-config.yaml", "w") as f:
        f.write(pre_commit_config.strip())
    
    print("✅ Created .pre-commit-config.yaml")

def create_github_instructions():
    """Create instructions for GitHub setup."""
    instructions = """
# 🚀 GitHub Repository Setup Instructions

Your Visey Recommender project is ready for GitHub! Follow these steps:

## 1. Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `visey-recommender`
3. Description: `AI-powered WordPress content recommendation system with real-time sync and modern web interface`
4. Set to Public (or Private if preferred)
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

## 2. Connect Local Repository to GitHub

Copy and run these commands in your terminal:

```bash
# Add GitHub remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/visey-recommender.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## 3. Set Up Repository Settings

### Branch Protection
1. Go to Settings → Branches
2. Add rule for `main` branch
3. Enable:
   - Require pull request reviews before merging
   - Require status checks to pass before merging
   - Require branches to be up to date before merging

### GitHub Actions
The CI/CD workflows are already configured in `.github/workflows/`

### Repository Topics
Add these topics to help others discover your project:
- `ai`
- `machine-learning`
- `wordpress`
- `recommendation-system`
- `fastapi`
- `python`
- `docker`
- `kubernetes`

### Repository Description
```
AI-powered WordPress content recommendation system with real-time sync, load balancing, and modern web interface. Built with FastAPI, featuring intelligent caching, multiple algorithms, and production-ready deployment options.
```

### Website URL
```
https://your-username.github.io/visey-recommender
```

## 4. Enable GitHub Features

### Issues
- Enable issue templates (already configured)
- Set up labels for better organization

### Discussions
- Enable GitHub Discussions for community Q&A

### Security
- Enable security advisories
- Set up Dependabot for dependency updates

### Pages (Optional)
- Enable GitHub Pages for documentation hosting
- Use `docs/` folder or `gh-pages` branch

## 5. Post-Setup Tasks

### README Badges
Update the badges in README.md with your repository URL:
```markdown
[![Tests](https://github.com/YOUR_USERNAME/visey-recommender/workflows/Tests/badge.svg)](https://github.com/YOUR_USERNAME/visey-recommender/actions)
[![Docker](https://github.com/YOUR_USERNAME/visey-recommender/workflows/Docker/badge.svg)](https://github.com/YOUR_USERNAME/visey-recommender/actions)
```

### Documentation
- Update all instances of `yourusername` in documentation
- Add your contact information
- Update license if needed

### Secrets (for CI/CD)
Add these secrets in Settings → Secrets and variables → Actions:
- `DOCKER_USERNAME` - Your Docker Hub username
- `DOCKER_PASSWORD` - Your Docker Hub password
- `WP_BASE_URL` - Test WordPress URL for CI
- `WP_USERNAME` - Test WordPress username
- `WP_PASSWORD` - Test WordPress password

## 6. First Release

After pushing to GitHub:

1. Go to Releases → Create a new release
2. Tag version: `v1.0.0`
3. Release title: `Visey Recommender v1.0.0 - Initial Release`
4. Copy description from CHANGELOG.md
5. Attach any binary assets if needed
6. Publish release

## 7. Community Setup

### Contributing
- Review CONTRIBUTING.md
- Set up issue templates
- Create discussion categories

### License
- Verify MIT license is appropriate
- Update copyright year and holder

### Code of Conduct
Consider adding a CODE_OF_CONDUCT.md file

## 8. Marketing Your Project

### Social Media
Share your project on:
- Twitter/X with hashtags: #AI #WordPress #OpenSource #Python
- LinkedIn with a detailed post
- Reddit communities: r/Python, r/MachineLearning, r/WordPress
- Dev.to with a detailed article

### Documentation Site
Consider setting up:
- GitHub Pages for documentation
- ReadTheDocs integration
- Demo site deployment

## 🎉 You're Ready!

Your Visey Recommender project is now ready for the world! 

Key URLs after setup:
- Repository: https://github.com/YOUR_USERNAME/visey-recommender
- Issues: https://github.com/YOUR_USERNAME/visey-recommender/issues
- Actions: https://github.com/YOUR_USERNAME/visey-recommender/actions
- Releases: https://github.com/YOUR_USERNAME/visey-recommender/releases

Happy coding! 🚀
"""
    
    with open("GITHUB_SETUP.md", "w") as f:
        f.write(instructions.strip())
    
    print("✅ Created GITHUB_SETUP.md with detailed instructions")

def main():
    """Main setup function."""
    print("🚀 Setting up Visey Recommender for GitHub")
    print("=" * 50)
    
    # Check if Git is installed
    if not check_git_installed():
        print("❌ Git is not installed. Please install Git first.")
        print("   Download from: https://git-scm.com/downloads")
        return False
    
    # Check if already a Git repository
    if Path(".git").exists():
        print("⚠️  Git repository already exists")
        response = input("Do you want to continue? This will add and commit all changes. (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("Setup cancelled")
            return False
    else:
        # Initialize Git repository
        initialize_git_repo()
    
    # Update .gitignore
    create_gitignore_additions()
    
    # Set up pre-commit
    setup_pre_commit()
    
    # Create GitHub setup instructions
    create_github_instructions()
    
    # Final Git operations
    print("\n🔧 Adding new files to Git...")
    run_command("git add .")
    
    # Check if there are changes to commit
    result = run_command("git diff --cached --quiet", check=False)
    if result.returncode != 0:  # There are changes
        run_command('git commit -m "docs: add GitHub setup files and pre-commit configuration"')
        print("✅ Committed setup files")
    else:
        print("✅ No new changes to commit")
    
    print("\n" + "=" * 50)
    print("🎉 GitHub setup completed!")
    print("\n📋 Next steps:")
    print("1. Read GITHUB_SETUP.md for detailed instructions")
    print("2. Create a new repository on GitHub")
    print("3. Connect your local repository to GitHub")
    print("4. Push your code to GitHub")
    print("\n💡 Quick start:")
    print("   git remote add origin https://github.com/YOUR_USERNAME/visey-recommender.git")
    print("   git branch -M main")
    print("   git push -u origin main")
    print("\n🔗 Don't forget to:")
    print("   - Update YOUR_USERNAME in the commands above")
    print("   - Set up repository settings and branch protection")
    print("   - Add repository topics and description")
    print("   - Enable GitHub features (Issues, Discussions, etc.)")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)