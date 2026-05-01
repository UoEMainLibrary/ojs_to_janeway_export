#!/usr/bin/python3
# @name: export_editorial.py
# @creation_date: 2026-05-01
# @license: The MIT License <https://opensource.org/licenses/MIT>
# @author: Simon Bowie <simonxix@simonxix.com>
# @purpose: export public-facing editorial team details from an OJS journal to Janeway Import CSV
# @acknowledgements:
# https://github.com/openlibhums/imports 
# https://janeway-imports.readthedocs.io/en/latest/editorial_team_import.html

import argparse
from ojs_api import fetch_editorial_users
from janeway_csv import editorial_users_to_rows, write_editorial_csv

def main():
    parser = argparse.ArgumentParser(description="Export OJS editorial team to Janeway CSV.")
    parser.add_argument("--base-url", required=True, help="OJS site root URL, e.g. https://example.org")
    parser.add_argument("--journal-path", required=True, help="OJS journal path, e.g. mat")
    parser.add_argument("--api-key", required=True, help="OJS API key")
    parser.add_argument("--locale", default="en", help="Preferred locale (default: en)")
    parser.add_argument("--output", default="/output/janeway_editorial.csv", help="Output CSV path")
    args = parser.parse_args()

    journal_url = f"{args.base_url.rstrip('/')}/{args.journal_path.strip('/')}"

    print("Fetching editorial team...")
    users = fetch_editorial_users(journal_url, args.api_key)
    print(f"  Found {len(users)} user(s) with editorial roles")

    rows = editorial_users_to_rows(users, args.locale)
    write_editorial_csv(rows, args.output)
    print(f"Editorial team CSV written to {args.output} ({len(rows)} row(s)).")
    print("Upload via Janeway > Manager > Plugins > Import Plugin > Editorial Team Import")

if __name__ == "__main__":
    main()
