#!/usr/bin/python3
# @name: list_issues.py
# @creation_date: 2026-05-01
# @license: The MIT License <https://opensource.org/licenses/MIT>
# @author: Simon Bowie <simonxix@simonxix.com>
# @purpose: list published issues from an OJS journal for getting IDs
# @acknowledgements:
# https://docs.pkp.sfu.ca/dev/api/ojs/3.4

import argparse
from ojs_api import fetch_all_issues, detect_context_id, get_locale_value

def main():
    parser = argparse.ArgumentParser(description="List OJS issues.")
    parser.add_argument("--base-url", required=True, help="OJS site root URL, e.g. https://example.org")
    parser.add_argument("--journal-path", required=True, help="OJS journal path, e.g. mat")
    parser.add_argument("--api-key", required=True, help="OJS API key")
    args = parser.parse_args()

    journal_url = f"{args.base_url.rstrip('/')}/{args.journal_path.strip('/')}"

    print("Fetching issues...")
    issues = fetch_all_issues(journal_url, args.api_key)
    if not issues:
        print("No published issues found.")
        return

    context_id = detect_context_id(journal_url, args.api_key, issues)
    if context_id:
        print(f"  Journal context ID: {context_id}")
    else:
        print("  Journal context ID: could not detect — check your OJS cover image URLs")

    print(f"\n{'ID':>6}  {'Vol':>4}  {'No':>4}  {'Year':>6}  Title")
    print("-" * 60)
    for issue in sorted(issues, key=lambda x: x.get("id", 0)):
        title = get_locale_value(issue.get("title"))
        vol = str(issue.get("volume", ""))
        num = str(issue.get("number", ""))
        year = str(issue.get("year", "") or "")
        print(f"{issue['id']:>6}  {vol:>4}  {num:>4}  {year:>6}  {title}")

if __name__ == "__main__":
    main()
