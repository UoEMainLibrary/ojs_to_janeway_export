#!/usr/bin/python3
# @name: export_issue.py
# @creation_date: 2026-05-01
# @license: The MIT License <https://opensource.org/licenses/MIT>
# @author: Simon Bowie <simonxix@simonxix.com>
# @purpose: export a single issue of an OJS journal to Janeway Import CSV (and also images accompanying articles)
# @acknowledgements:
# https://github.com/openlibhums/imports 
# https://janeway-imports.readthedocs.io/en/latest/import_export_update.html
# https://janeway-imports.readthedocs.io/en/latest/article_images.html

import argparse
from ojs_api import (
    fetch_issue, fetch_submissions_for_issue, build_section_cache,
    get_current_publication, get_pdf_url, get_cover_image_url,
    get_locale_value,
)
from janeway_csv import submission_to_rows, write_article_csv, write_images_csv

def main():
    parser = argparse.ArgumentParser(description="Export an OJS issue to Janeway import CSVs.")
    parser.add_argument("--base-url", required=True, help="OJS site root URL, e.g. https://example.org")
    parser.add_argument("--journal-path", required=True, help="OJS journal path, e.g. mat")
    parser.add_argument("--api-key", required=True, help="OJS API key")
    parser.add_argument("--issue-id", required=True, type=int, help="OJS issue ID")
    parser.add_argument("--journal-code", required=True, help="Janeway journal code")
    parser.add_argument("--context-id", default="", help="OJS journal context ID (for cover images)")
    parser.add_argument("--locale", default="en", help="Preferred locale (default: en)")
    parser.add_argument("--output", default="/output/janeway_import.csv", help="Article CSV output path")
    parser.add_argument("--images-output", default="", help="Article images CSV output path")
    args = parser.parse_args()

    journal_url = f"{args.base_url.rstrip('/')}/{args.journal_path.strip('/')}"

    print(f"Fetching issue {args.issue_id}...")
    issue = fetch_issue(journal_url, args.api_key, args.issue_id)
    print(f"  Found: Vol. {issue.get('volume')} No. {issue.get('number')} ({issue.get('year', '')})")

    print("Fetching submissions...")
    section_cache = build_section_cache(journal_url, args.api_key, args.issue_id, args.locale)
    submissions = fetch_submissions_for_issue(journal_url, args.api_key, args.issue_id)
    print(f"  Found {len(submissions)} published submission(s)")

    all_rows = []
    image_rows = []
    for i, sub in enumerate(submissions, 1):
        pub_stub = (sub.get("publications") or [{}])[-1]
        title_preview = get_locale_value(
            pub_stub.get("fullTitle") or pub_stub.get("title"), args.locale
        )[:60] or f"submission {sub['id']}"
        print(f"  [{i}/{len(submissions)}] {title_preview}...")

        rows, doi, cover_image_url = submission_to_rows(
            journal_url, args.base_url, args.api_key,
            sub, issue, args.journal_code, args.locale, args.context_id,
            section_cache,
            get_current_publication,
            get_pdf_url,
            get_cover_image_url,
        )
        all_rows.extend(rows)
        if cover_image_url and doi:
            image_rows.append({"Identifier Type": "doi", "Identifier": doi, "URL": cover_image_url})

    print(f"\nWriting {len(all_rows)} row(s) to {args.output}...")
    write_article_csv(all_rows, args.output)
    print(f"Done. Upload {args.output} via Janeway → All Articles → Upload Update.")

    if args.images_output:
        image_rows_with_images = [r for r in image_rows if r["URL"]]
        if image_rows_with_images:
            write_images_csv(image_rows_with_images, args.images_output)
            print(f"Images CSV written to {args.images_output} ({len(image_rows_with_images)} article(s)).")
            print("Upload via Janeway → Imports Plugin → Article Images.")
        else:
            print("No cover images found — images CSV not written.")

if __name__ == "__main__":
    main()
