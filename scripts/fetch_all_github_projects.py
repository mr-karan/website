#!/usr/bin/env uv run
# /// script
# dependencies = ["requests"]
# ///

"""
Fetch all public GitHub repositories for a user and generate TOML entries.
Sorts repositories by last updated date in descending order.

Usage:
    uv run scripts/fetch_all_github_projects.py [username]
    
Example:
    uv run scripts/fetch_all_github_projects.py mr-karan
"""

import json
import sys
import time
from datetime import datetime
import requests

def fetch_all_repos(username: str) -> list:
    """
    Fetch all public repositories for a GitHub user.
    
    Args:
        username: GitHub username
        
    Returns:
        List of repository data
    """
    repos = []
    page = 1
    per_page = 100
    
    print(f"Fetching repositories for {username}...", file=sys.stderr)
    
    while True:
        url = f"https://api.github.com/users/{username}/repos"
        params = {
            'page': page,
            'per_page': per_page,
            'type': 'owner',
            'sort': 'pushed',
            'direction': 'desc'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                break
                
            repos.extend(data)
            
            print(f"  Fetched page {page} ({len(data)} repos)", file=sys.stderr)
            
            if len(data) < per_page:
                break
                
            page += 1
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            print(f"Error fetching repos: {e}", file=sys.stderr)
            break
    
    return repos

def format_date(date_str: str) -> str:
    """
    Format ISO date string to Month Year format.
    
    Args:
        date_str: ISO format date string
        
    Returns:
        Formatted date string (e.g., "Jan 2024")
    """
    if not date_str:
        return ""
    
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime("%b %Y")
    except:
        return ""

def should_include_repo(repo: dict) -> bool:
    """
    Filter to determine if a repository should be included.
    
    Args:
        repo: Repository data from GitHub API
        
    Returns:
        True if the repo should be included
    """
    # Skip forks
    if repo.get('fork', False):
        return False
    
    # Skip repos with no description
    if not repo.get('description'):
        return False
    
    # Skip archived repos
    if repo.get('archived', False):
        return False
    
    return True

def generate_toml_entry(repo: dict) -> str:
    """
    Generate a TOML entry for a repository.
    
    Args:
        repo: Repository data from GitHub API
        
    Returns:
        TOML formatted string
    """
    lines = []
    lines.append("[[project]]")
    lines.append(f'name = "{repo["name"]}"')
    
    # Clean up description
    description = repo.get("description", "").replace('"', '\\"')
    lines.append(f'description = "{description}"')
    
    # Add created and pushed dates
    created_date = format_date(repo.get("created_at", ""))
    pushed_date = format_date(repo.get("pushed_at", ""))
    
    if created_date:
        lines.append(f'created = "{created_date}"')
    if pushed_date:
        lines.append(f'pushed = "{pushed_date}"')
    
    # Add star count if significant
    stars = repo.get("stargazers_count", 0)
    if stars > 10:
        lines.append(f'stars = {stars}')
    
    # Add language if present
    language = repo.get("language", "")
    if language:
        lines.append(f'language = "{language}"')
    
    lines.append('links = [')
    
    # Add homepage if exists
    homepage = repo.get("homepage", "")
    if homepage and homepage.strip():
        lines.append(f'  {{ name = "Homepage", url = "{homepage}" }},')
    
    # Add GitHub link
    lines.append(f'  {{ name = "GitHub", url = "{repo["html_url"]}" }},')
    lines.append(']')
    
    return '\n'.join(lines)

def main():
    """Main function to process repositories."""
    
    # Get username from command line or default
    username = sys.argv[1] if len(sys.argv) > 1 else "mr-karan"
    
    # Fetch all repositories
    repos = fetch_all_repos(username)
    
    if not repos:
        print("No repositories found", file=sys.stderr)
        sys.exit(1)
    
    # Filter repositories
    filtered_repos = [repo for repo in repos if should_include_repo(repo)]
    
    # Sort by pushed_at in descending order (most recently pushed first)
    filtered_repos.sort(key=lambda x: x.get('pushed_at', ''), reverse=True)
    
    print(f"Found {len(repos)} total repos, including {len(filtered_repos)} non-fork repos", file=sys.stderr)
    
    # Generate TOML output
    print("# GitHub Projects")
    print(f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"# Total projects: {len(filtered_repos)}")
    print("")
    
    for repo in filtered_repos:
        print(generate_toml_entry(repo))
        print()

if __name__ == "__main__":
    main()