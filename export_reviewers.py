#!/usr/bin/python3
# @name: export_reviewers.py
# @creation_date: 2026-05-01
# @license: The MIT License <https://opensource.org/licenses/MIT>
# @author: Simon Bowie <simonxix@simonxix.com>
# @purpose: export reviewers from an OJS journal to Janeway Import CSV
# @acknowledgements:
# https://github.com/openlibhums/imports 
# https://janeway-imports.readthedocs.io/en/latest/reviewer_import.html

import argparse
from ojs_api import fetch_reviewer_users
from janeway_csv import write_reviewers_csv

def main():
    parser = argparse.ArgumentParser(description="Export OJS reviewers to Janeway CSV.")
    parser.add_argument("--base-url", required=True, help="OJS site root URL, e.g. https://example.org")
    parser.add_argument("--journal-path", required=True, help="OJS journal path, e.g. mat")
    parser.add_argument("--api-key", required=True, help="OJS API key")
    parser.add_argument("--locale", default="en", help="Preferred locale (default: en)")
    parser.add_argument("--output", default="/output/janeway_reviewers.csv", help="Output CSV path")
    args = parser.parse_args()

    journal_url = f"{args.base_url.rstrip('/')}/{args.journal_path.strip('/')}"

    print("Fetching reviewers...")
    users = fetch_reviewer_users(journal_url, args.api_key)
    count = write_reviewers_csv(users, args.output, args.locale)
    print(f"Reviewers CSV written to {args.output} ({count} user(s)).")
    print("Upload via Janeway > Manager > Plugins > Import Plugin > Reviewers Import")

if __name__ == "__main__":
    main()
