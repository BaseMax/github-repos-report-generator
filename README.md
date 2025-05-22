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

## License

MIT License © 2025 Max Base
