# GitHub User Repositories Exporter

A Python CLI tool to fetch all public repositories of a GitHub user, extracting repository details such as name, URL, description, top language, and tags. Outputs data in CSV, JSON, and HTML formats.

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

```bash
pip install requests pandas jinja2
```

## Usage

```bash
python github_user_repos.py <username_or_url> [--token YOUR_GITHUB_TOKEN] [--output-dir path/to/save]
```

Examples:

```bash
python github_user_repos.py @octocat
python github_user_repos.py https://github.com/octocat --token ghp_yourtoken123 --output-dir ./output
```

## Testing

I have up to 2k repositories while about 1k of these are public, so let's try the project and script on my account to make sure it's handling things properly.

```bash
$ python github_user_repos.py basemax
[INFO] Detected username: basemax
[INFO] User 'basemax' validated. Fetching repositories...
[INFO] Fetching repositories...
[INFO] Page 1: Retrieved 100 repositories
[INFO] Page 2: Retrieved 100 repositories
[INFO] Page 3: Retrieved 100 repositories
[INFO] Page 4: Retrieved 100 repositories
[INFO] Page 5: Retrieved 100 repositories
[INFO] Page 6: Retrieved 100 repositories
[INFO] Page 7: Retrieved 100 repositories
[INFO] Page 8: Retrieved 100 repositories
[INFO] Page 9: Retrieved 14 repositories
[INFO] Total public repositories found: 814
```

## License

MIT License © 2025 Max Base
