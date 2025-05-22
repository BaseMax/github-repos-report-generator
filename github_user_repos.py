import re
import sys
import time
import json
import logging
import argparse
import requests
import pandas as pd
from typing import List, Dict, Tuple, Optional
from jinja2 import Template

GITHUB_API = "https://api.github.com"

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def clean_username(input_str: str) -> str:
    """Extract and clean GitHub username from input string."""
    input_str = input_str.strip()
    if input_str.startswith("@"):
        input_str = input_str[1:]
    m = re.search(r"github\.com/([^/]+)", input_str, re.IGNORECASE)
    if m:
        input_str = m.group(1)
    return input_str.strip()


def request_with_retries(url: str, headers: Dict[str, str] = None, params: Dict = None,
                         max_retries: int = 3, delay: float = 1.0) -> Optional[requests.Response]:
    """Make a GET request with retries and delay."""
    headers = headers or {}
    params = params or {}

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            if resp.status_code == 200:
                return resp
            elif resp.status_code == 404:
                return resp
            else:
                logger.warning(f"HTTP {resp.status_code} from {url}. Attempt {attempt}/{max_retries}")
        except requests.RequestException as e:
            logger.warning(f"Request exception on {url}: {e}. Attempt {attempt}/{max_retries}")
        time.sleep(delay)
    return None


def validate_username(username: str, token: Optional[str] = None) -> Tuple[bool, Optional[Dict]]:
    """Check if username exists and is a user (not org)."""
    url = f"{GITHUB_API}/users/{username}"
    headers = {"Authorization": f"token {token}"} if token else {}
    response = request_with_retries(url, headers=headers)
    if not response:
        return False, "Failed to fetch user info after retries"
    if response.status_code == 404:
        return False, "User not found"
    data = response.json()
    if data.get("type") != "User":
        return False, f"Account is not a user (type={data.get('type')})"
    return True, data


def get_all_repos(username: str, token: Optional[str] = None) -> List[Dict]:
    """Fetch all public repositories of user with pagination."""
    repos = []
    page = 1
    per_page = 100
    headers = {"Authorization": f"token {token}"} if token else {}

    logger.info("Fetching repositories...")
    while True:
        url = f"{GITHUB_API}/users/{username}/repos"
        params = {"per_page": per_page, "page": page, "type": "public", "sort": "full_name"}
        response = request_with_retries(url, headers=headers, params=params)
        if not response or response.status_code != 200:
            logger.error(f"Failed to fetch repos page {page}. Status: {response.status_code if response else 'No response'}")
            break
        page_data = response.json()
        if not page_data:
            break
        repos.extend(page_data)
        logger.info(f"Page {page}: Retrieved {len(page_data)} repositories")
        page += 1
        time.sleep(0.1)
    return repos


def get_repo_topics(owner: str, repo_name: str, token: Optional[str] = None) -> List[str]:
    """Get topics/tags of a repository."""
    url = f"{GITHUB_API}/repos/{owner}/{repo_name}/topics"
    headers = {"Accept": "application/vnd.github.mercy-preview+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    response = request_with_retries(url, headers=headers)
    if response and response.status_code == 200:
        return response.json().get("names", [])
    return []


def extract_repo_info(repo: Dict, token: Optional[str] = None) -> Dict:
    """Extract relevant repo info."""
    owner = repo.get("owner", {}).get("login", "")
    name = repo.get("name", "")
    return {
        "name": name,
        "url": repo.get("html_url", ""),
        "description": repo.get("description") or "",
        "top_language": repo.get("language") or "",
        "tags": get_repo_topics(owner, name, token)
    }


def save_csv(data: List[Dict], filename: str) -> None:
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    logger.info(f"Saved CSV to {filename}")


def save_json(data: List[Dict], filename: str) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved JSON to {filename}")


def save_html(data: List[Dict], filename: str, username: str) -> None:
    template_str = """
    <html>
    <head>
      <meta charset="UTF-8" />
      <title>GitHub Repositories of {{ username }}</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
        th { background-color: #f4f4f4; }
      </style>
    </head>
    <body>
    <h1>Public Repositories of GitHub User: {{ username }}</h1>
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>URL</th>
          <th>Description</th>
          <th>Top Language</th>
          <th>Tags</th>
        </tr>
      </thead>
      <tbody>
      {% for repo in repos %}
        <tr>
          <td>{{ repo.name }}</td>
          <td><a href="{{ repo.url }}" target="_blank">{{ repo.url }}</a></td>
          <td>{{ repo.description }}</td>
          <td>{{ repo.top_language }}</td>
          <td>{{ repo.tags | join(', ') }}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
    </body>
    </html>
    """
    template = Template(template_str)
    html_content = template.render(repos=data, username=username)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.info(f"Saved HTML report to {filename}")


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch public GitHub repositories info for a user.")
    parser.add_argument("username", help="GitHub username, @username, or full GitHub profile URL")
    parser.add_argument("--token", help="GitHub API token to increase rate limit", default=None)
    parser.add_argument("--output-dir", help="Directory to save output files", default=".")
    return parser.parse_args()


def main():
    args = parse_args()

    username = clean_username(args.username)
    logger.info(f"Detected username: {username}")

    valid, user_data_or_err = validate_username(username, token=args.token)
    if not valid:
        logger.error(f"Validation failed: {user_data_or_err}")
        sys.exit(1)

    logger.info(f"User '{username}' validated. Fetching repositories...")
    repos = get_all_repos(username, token=args.token)
    logger.info(f"Total public repositories found: {len(repos)}")

    repo_infos = [extract_repo_info(repo, token=args.token) for repo in repos]

    output_dir = args.output_dir.rstrip("/\\")
    csv_path = f"{output_dir}/{username}_repos.csv"
    json_path = f"{output_dir}/{username}_repos.json"
    html_path = f"{output_dir}/{username}_repos.html"

    save_csv(repo_infos, csv_path)
    save_json(repo_infos, json_path)
    save_html(repo_infos, html_path, username)

    logger.info("All files saved successfully.")


if __name__ == "__main__":
    main()
