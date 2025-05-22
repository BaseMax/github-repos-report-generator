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
from datetime import datetime
from colorama import init as colorama_init, Fore, Style

colorama_init(autoreset=True)

GITHUB_API = "https://api.github.com"

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def log_repo_info(repo_info: Dict):
    print(
        Fore.CYAN + "[Repo]" + Style.RESET_ALL + "\n" +
        f"  {Fore.YELLOW}name       :{Style.RESET_ALL} {repo_info['name']}\n"
        f"  {Fore.YELLOW}url        :{Style.RESET_ALL} {repo_info['url']}\n"
        f"  {Fore.YELLOW}description:{Style.RESET_ALL} {repo_info['description']}\n"
        f"  {Fore.YELLOW}language   :{Style.RESET_ALL} {repo_info['top_language']}\n"
        f"  {Fore.YELLOW}tags       :{Style.RESET_ALL} {', '.join(repo_info['tags']) if repo_info['tags'] else 'None'}"
    )


def log_page_info(page: int, count: int):
    print(Fore.GREEN + f"Page {page}: Retrieved {count} repositories" + Style.RESET_ALL)


def init_repo_text_file(filepath: str):
    """Create or clear the repo info text file at the start."""
    with open(filepath, "w", encoding="utf-8") as f:
        pass


def append_repo_info_to_file(filepath: str, repo_info: Dict, page: int, index: int):
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"[Repo] (Page {page}, Index {index})\n")
        f.write(f"  name       : {repo_info['name']}\n")
        f.write(f"  url        : {repo_info['url']}\n")
        f.write(f"  description: {repo_info['description']}\n")
        f.write(f"  language   : {repo_info['top_language']}\n")
        tags_str = ', '.join(repo_info['tags']) if repo_info['tags'] else 'None'
        f.write(f"  tags       : {tags_str}\n\n")


def clean_username(input_str: str) -> str:
    """Extract and clean GitHub username from input string."""
    input_str = input_str.strip()
    if input_str.startswith("@"):
        input_str = input_str[1:]
    m = re.search(r"github\.com/([^/]+)", input_str, re.IGNORECASE)
    if m:
        input_str = m.group(1)
    return input_str.strip()


def sleep_until(reset_epoch: int):
    """Sleep until the reset time given by GitHub API."""
    now = int(time.time())
    sleep_seconds = reset_epoch - now + 1
    if sleep_seconds > 0:
        reset_time_str = datetime.utcfromtimestamp(reset_epoch).strftime('%Y-%m-%d %H:%M:%S UTC')
        logger.warning(f"Rate limit reached. Sleeping for {sleep_seconds}s until {reset_time_str}")
        time.sleep(sleep_seconds)


def request_with_retries(url: str, headers: Dict[str, str] = None, params: Dict = None,
                         max_retries: int = 5, delay: float = 1.0, token: Optional[str] = None) -> Optional[requests.Response]:
    """Make a GET request with retries and adaptive delay based on rate limits."""
    headers = headers or {}
    params = params or {}

    if token:
        headers["Authorization"] = f"token {token}"

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            remaining = resp.headers.get("X-RateLimit-Remaining")
            reset = resp.headers.get("X-RateLimit-Reset")
            retry_after = resp.headers.get("Retry-After")

            if remaining == "0":
                if reset:
                    reset_epoch = int(reset)
                    sleep_until(reset_epoch)
                else:
                    logger.warning("Rate limit exceeded, but no reset header found. Sleeping for 60 seconds.")
                    time.sleep(60)
                continue

            if resp.status_code in (403, 429):
                if retry_after:
                    retry_after_seconds = int(retry_after)
                    logger.warning(f"Secondary rate limit hit. Sleeping for Retry-After: {retry_after_seconds} seconds.")
                    time.sleep(retry_after_seconds)
                    continue
                elif remaining == "0" and reset:
                    reset_epoch = int(reset)
                    sleep_until(reset_epoch)
                    continue
                else:
                    backoff = delay * (2 ** (attempt - 1))
                    logger.warning(f"Rate limited with status {resp.status_code}. Backoff sleeping for {backoff} seconds.")
                    time.sleep(backoff)
                    continue

            if resp.status_code in (200, 404):
                return resp

            logger.warning(f"HTTP {resp.status_code} from {url}. Attempt {attempt}/{max_retries}")
        except requests.RequestException as e:
            logger.warning(f"Request exception on {url}: {e}. Attempt {attempt}/{max_retries}")

        time.sleep(delay)
    return None


def validate_username(username: str, token: Optional[str] = None) -> Tuple[bool, Optional[Dict]]:
    """Check if username exists and is a user (not org)."""
    url = f"{GITHUB_API}/users/{username}"
    response = request_with_retries(url, token=token)
    if not response:
        return False, "Failed to fetch user info after retries"
    if response.status_code == 404:
        return False, "User not found"
    data = response.json()
    if data.get("type") != "User":
        return False, f"Account is not a user (type={data.get('type')})"
    return True, data


def get_all_repos(username: str, token: Optional[str] = None, text_file_path: Optional[str] = None) -> List[Dict]:
    repos = []
    page = 1
    per_page = 100
    logger.info("Fetching repositories...")

    if text_file_path:
        init_repo_text_file(text_file_path)

    while True:
        url = f"{GITHUB_API}/users/{username}/repos"
        params = {
            "per_page": per_page,
            "page": page,
            "type": "public",
            "sort": "created",
            "direction": "asc"
        }
        response = request_with_retries(url, params=params, token=token)
        if not response or response.status_code != 200:
            logger.error(f"Failed to fetch repos page {page}. Status: {response.status_code if response else 'No response'}")
            break
        page_data = response.json()
        if not page_data:
            break

        for i, repo in enumerate(page_data, start=1):
            owner = repo.get("owner", {}).get("login", "")
            name = repo.get("name", "")
            topics = get_repo_topics(owner, name, token)
            repo["topics"] = topics

            repo_info = extract_repo_info(repo, topics)
            log_repo_info(repo_info)
            if text_file_path:
                append_repo_info_to_file(text_file_path, repo_info, page, i)

        repos.extend(page_data)

        log_page_info(page, len(page_data))
        page += 1
        time.sleep(0.1)
    return repos


def get_repo_topics(owner: str, repo_name: str, token: Optional[str] = None) -> List[str]:
    """Get topics/tags of a repository."""
    url = f"{GITHUB_API}/repos/{owner}/{repo_name}/topics"
    headers = {"Accept": "application/vnd.github.mercy-preview+json"}
    response = request_with_retries(url, headers=headers, token=token)
    if response and response.status_code == 200:
        return response.json().get("names", [])
    return []


def extract_repo_info(repo: Dict, topics: List[str]) -> Dict:
    owner = repo.get("owner", {}).get("login", "")
    name = repo.get("name", "")
    return {
        "name": name,
        "url": repo.get("html_url", ""),
        "description": repo.get("description") or "",
        "top_language": repo.get("language") or "",
        "tags": topics
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
    <footer>
      <p>Generated on {{ now.strftime('%Y-%m-%d %H:%M:%S') }}</p>
        <p>GitHub User: {{ username }}</p>
        <p>Data Source: GitHub API</p>
        <p>Report generated by <a href="https://github.com/BaseMax/github-repos-report-generator">github-repos-report-generator</a></p>
    </footer>
    </body>
    </html>
    """
    template = Template(template_str)
    now = datetime.now()
    html_content = template.render(repos=data, username=username, now=now)
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

    if args.token:
        logger.info("Using provided GitHub API token.")
    else:
        logger.warning("No GitHub API token provided. Rate limits may apply.")

    valid, user_data_or_err = validate_username(username, token=args.token)
    if not valid:
        logger.error(f"Validation failed: {user_data_or_err}")
        sys.exit(1)

    output_dir = args.output_dir.rstrip("/\\")
    csv_path = f"{output_dir}/{username}_repos.csv"
    json_path = f"{output_dir}/{username}_repos.json"
    html_path = f"{output_dir}/{username}_repos.html"
    txt_path = f"{output_dir}/{username}_repos.txt"

    logger.info(f"User '{username}' validated. Fetching repositories...")

    repos = get_all_repos(username, token=args.token, text_file_path=txt_path)
    logger.info(f"Total public repositories found: {len(repos)}")

    repo_infos = [extract_repo_info(repo, repo.get("topics", [])) for repo in repos]

    save_csv(repo_infos, csv_path)
    save_json(repo_infos, json_path)
    save_html(repo_infos, html_path, username)

    logger.info("All files saved successfully.")


if __name__ == "__main__":
    main()
