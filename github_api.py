"""
GitHub API interactions
"""
import requests
from datetime import datetime

API_URL = "https://api.github.com/graphql"


def test_github_auth(username, token):
    """Test GitHub authentication"""
    query = """
    {
      viewer {
        login
      }
    }
    """
    response = requests.post(
        API_URL,
        json={"query": query},
        headers={"Authorization": f"bearer {token}"}
    )
    data = response.json()
    return "errors" not in data and data.get("data", {}).get("viewer", {}).get("login") is not None


def _get_user_creation_year(username, token):
    """Get user account creation year"""
    user_info_query = f"""
    {{
        user(login: "{username}") {{
            createdAt
        }}
    }}
    """
    
    response = requests.post(API_URL, json={'query': user_info_query}, headers={'Authorization': f'bearer {token}'})
    user_data = response.json()
    
    if 'errors' in user_data:
        return None
    
    created_at = user_data['data']['user']['createdAt']
    return datetime.fromisoformat(created_at.replace('Z', '+00:00')).year


def _build_current_year_query():
    """Build query for current year"""
    return """
        contributionsCollection {
            commitContributionsByRepository(maxRepositories: 100) {
                repository { nameWithOwner url isPrivate isFork }
            }
            pullRequestContributionsByRepository(maxRepositories: 100) {
                repository { nameWithOwner url isPrivate isFork }
            }
            issueContributionsByRepository(maxRepositories: 100) {
                repository { nameWithOwner url isPrivate isFork }
            }
            pullRequestReviewContributionsByRepository(maxRepositories: 100) {
                repository { nameWithOwner url isPrivate isFork }
            }
            repositoryContributions(first: 100) {
                edges { node { repository { nameWithOwner url isPrivate isFork } } }
            }
        }
    """


def _build_year_query(year):
    """Build query for a specific year"""
    return f"""
        contributionsCollection{year}: contributionsCollection(from: "{year}-01-01T00:00:00Z", to: "{year}-12-31T23:59:59Z") {{
            commitContributionsByRepository(maxRepositories: 100) {{
                repository {{ nameWithOwner url isPrivate isFork }}
            }}
            pullRequestContributionsByRepository(maxRepositories: 100) {{
                repository {{ nameWithOwner url isPrivate isFork }}
            }}
            repositoryContributions(first: 100) {{
                edges {{ node {{ repository {{ nameWithOwner url isPrivate isFork }} }} }}
            }}
        }}
    """


def _build_contributions_query(created_year, current_year):
    """Build complete query for all contributions"""
    contributions_queries = [_build_current_year_query()]
    
    for year in range(created_year, current_year):
        contributions_queries.append(_build_year_query(year))
    
    return f"""
    {{
        user(login: "{{username}}") {{
            {chr(10).join(contributions_queries)}
        }}
    }}
    """


def _fetch_contributions_data(username, token, query):
    """Fetch contributions data from GitHub API"""
    formatted_query = query.replace("{username}", username)
    response = requests.post(API_URL, json={'query': formatted_query}, headers={'Authorization': f'bearer {token}'})
    data = response.json()
    
    if 'errors' in data:
        return None
    
    return data['data']['user']


def _add_repo_if_valid(repo_set, repo, repos_all):
    """Add repository if valid (public and non-fork)"""
    if not repo['isPrivate'] and not repo['isFork']:
        repo_tuple = (repo['nameWithOwner'], repo['url'])
        repo_set.add(repo_tuple)
        repos_all.add(repo_tuple)


def _process_contribution_collection(cc, repos_commit, repos_pr, repos_all, is_current_year=False):
    """Process a contribution collection"""
    # Commits
    for item in cc.get('commitContributionsByRepository', []):
        _add_repo_if_valid(repos_commit, item['repository'], repos_all)

    # Pull requests
    for item in cc.get('pullRequestContributionsByRepository', []):
        _add_repo_if_valid(repos_pr, item['repository'], repos_all)

    # Issues and reviews (current year only)
    if is_current_year:
        for item in cc.get('issueContributionsByRepository', []):
            _add_repo_if_valid(set(), item['repository'], repos_all)

        for item in cc.get('pullRequestReviewContributionsByRepository', []):
            _add_repo_if_valid(set(), item['repository'], repos_all)

    # Repository contributions
    for edge in cc.get('repositoryContributions', {}).get('edges', []):
        _add_repo_if_valid(set(), edge['node']['repository'], repos_all)


def _extract_repositories_data(user_data):
    """Extract and organize repository data"""
    repos_all = set()
    repos_commit = set()
    repos_pr = set()

    for key, cc in user_data.items():
        if not key.startswith('contributionsCollection') or not cc:
            continue
        
        is_current_year = (key == 'contributionsCollection')
        _process_contribution_collection(cc, repos_commit, repos_pr, repos_all, is_current_year)

    repos_commit_only = {r for r in repos_commit if r not in repos_pr}
    repos_pr_only = repos_pr
    repos_other = repos_all - repos_commit - repos_pr

    return {
        'repos_commit_only': repos_commit_only,
        'repos_pr_only': repos_pr_only,
        'repos_other': repos_other
    }


def _build_readme_section(section_key, repos_set, user_comments, translator):
    """Build a README section"""
    if not repos_set:
        return []
    
    lines = [f"## {translator.get_text(section_key)}\n"]
    
    for name, url in sorted(repos_set):
        line = f"- [{name}]({url})"
        if name in user_comments:
            line += f" — {user_comments[name]}"
        lines.append(line)
    
    return lines


def _build_readme_content(username, repos_data, user_comments, translator):
    """Build complete README content"""
    lines = [f"# {translator.get_text('categories.profile_git')} : {username}\n"]

    # Commits only section
    commit_lines = _build_readme_section(
        'categories.commit_only', 
        repos_data['repos_commit_only'], 
        user_comments, 
        translator
    )
    lines.extend(commit_lines)

    # Pull requests section
    pr_lines = _build_readme_section(
        'categories.pull_requests', 
        repos_data['repos_pr_only'], 
        user_comments, 
        translator
    )
    if pr_lines:
        lines.append("")  # Empty line before section
        lines.extend(pr_lines)

    # Other contributions section
    other_lines = _build_readme_section(
        'categories.other_contributions', 
        repos_data['repos_other'], 
        user_comments, 
        translator
    )
    if other_lines:
        lines.append("")  # Empty line before section
        lines.extend(other_lines)

    return "\n".join(lines)


def generate_readme_content(username, token, user_comments, translator):
    """Generate README content based on GitHub contributions"""
    # Get user account creation year
    created_year = _get_user_creation_year(username, token)
    if created_year is None:
        return "", {}
    
    current_year = datetime.now().year
    
    # Build and execute query
    query = _build_contributions_query(created_year, current_year)
    user_data = _fetch_contributions_data(username, token, query)
    if user_data is None:
        return "", {}
    
    # Extract and organize data
    repos_data = _extract_repositories_data(user_data)
    
    # Build README content
    readme_content = _build_readme_content(username, repos_data, user_comments, translator)
    
    return readme_content, repos_data
