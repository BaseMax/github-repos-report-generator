# GitHub User Repositories Exporter

A powerful Python CLI tool to fetch all public repositories of a GitHub user, extracting detailed repository information such as name, URL, description, top programming language, and tags (topics). Outputs the collected data in CSV, JSON, and HTML formats for easy analysis and sharing.

---

## Features

- Accepts raw GitHub usernames, `@username`, or full GitHub profile URLs as input
- Validates user existence and confirms the user is not an organization
- Handles pagination to fetch all public repositories
- Retrieves repository topics (tags) using GitHub Topics API
- Supports GitHub personal access token for higher API rate limits
- Saves output data as CSV (UTF-8 with BOM), JSON, and a nicely formatted HTML report
- Provides informative logging and error handling
- Configurable output directory

---

## Installation

Clone this repository:

```bash
git clone https://github.com/BaseMax/github-repos-report-generator.git
cd github-repos-report-generator
```

(Optional but recommended) Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
or
pip install requests pandas jinja2
```

> **Dependencies include:** requests, pandas, jinja2, colorama

## Usage

```bash
python github_repos_exporter.py USERNAME_OR_URL [--token GITHUB_TOKEN] [--output-dir PATH]
```

- `USERNAME_OR_URL`: GitHub username, or with leading @, or a full GitHub profile URL (e.g., https://github.com/username).
- `--token` (optional): Your GitHub personal access token to increase API rate limits and avoid throttling.
- `--output-dir` (optional): Directory where the output files (.csv, .json, .html, .txt) will be saved. Defaults to current directory (.).

**Examples:**

```bash
python github_user_repos.py @octocat
```

```bash
python github_user_repos.py https://github.com/octocat --token ghp_yourtoken123 --output-dir ./output
```

## Output Files

Given username octocat and output directory ./output, the tool generates:

- `octocat_repos.csv` — Spreadsheet-friendly CSV with repository data
- `octocat_repos.json` — JSON file with detailed repository info
- `octocat_repos.html` — Beautiful HTML report listing repositories with clickable URLs
- `octocat_repos.txt` — Plain text log of repository info for quick reference

## Requirements

Python 3.7+

Internet connection

> Optional: GitHub Personal Access Token for increased API quota

## How It Works

- Input normalization: Extracts GitHub username from different input formats.
- User validation: Confirms user exists and is a "User" type (not an organization).
- Data retrieval: Calls GitHub API to fetch all public repositories (100 per page) with pagination.
- Topics fetching: For each repository, fetches tags/topics using GitHub's topics API.
- Rate limiting: Detects rate limit headers, waits automatically for reset, and retries requests.
- Output generation: Saves the results in CSV, JSON, and HTML formats for versatile use cases.

## Testing

I have up to 2,000 repositories at the moment, about 1,000 of which are public. Let's try the project and script on my account to make sure they handle everything properly.

```bash
$ python github_user_repos.py basemax
[INFO] Detected username: basemax
[INFO] User 'basemax' validated. Fetching repositories...
[INFO] Fetching repositories...
Page 1: Retrieved 100 repositories
Page 2: Retrieved 100 repositories
Page 3: Retrieved 100 repositories
Page 4: Retrieved 100 repositories
Page 5: Retrieved 100 repositories
Page 6: Retrieved 100 repositories
Page 7: Retrieved 100 repositories
Page 8: Retrieved 100 repositories
Page 9: Retrieved 14 repositories
[INFO] Total public repositories found: 814
[INFO] Saved CSV to ./basemax_repos.csv
[INFO] Saved JSON to ./basemax_repos.json
[INFO] Saved HTML report to ./basemax_repos.html
[INFO] All files saved successfully.
[INFO] Total public repositories found: 814
```

## Contributions & Issues

Feel free to open issues or submit pull requests to improve the tool. Your contributions are welcome!

## Contact

Developed by BaseMax

For questions or support, please open an issue on GitHub.

## License

MIT License © 2025 Max Base
