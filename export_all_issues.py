#!/usr/bin/python3
# @name: export_issue.py
# @creation_date: 2026-05-14
# @license: The MIT License <https://opensource.org/licenses/MIT>
# @author: Simon Bowie <simonxix@simonxix.com>
# @purpose: export all published articles from a journal to Janeway Import CSV (and also images accompanying articles)
# @acknowledgements:
# https://github.com/openlibhums/imports 
# https://janeway-imports.readthedocs.io/en/latest/import_export_update.html
# https://janeway-imports.readthedocs.io/en/latest/article_images.html

import argparse
import os
from ojs_api import (
    fetch_all_issues, fetch_submissions_for_issue, build_section_cache,
    get_current_publication, get_pdf_url, get_html_url, get_cover_image_url,
    get_locale_value,
)
from janeway_csv import submission_to_rows, write_article_csv, write_images_csv

def main():
    parser = argparse.ArgumentParser(
        description="Export all published OJS articles to Janeway import CSVs."
    )
    parser.add_argument("--base-url", required=True, help="OJS site root URL, e.g. https://example.org")
    parser.add_argument("--journal-path", required=True, help="OJS journal path, e.g. mat")
    parser.add_argument("--api-key", required=True, help="OJS API key")
    parser.add_argument("--journal-code", required=True, help="Janeway journal code")
    parser.add_argument("--context-id", default="", help="OJS journal context ID (for cover images)")
    parser.add_argument("--locale", default="en", help="Preferred locale (default: en)")
    parser.add_argument("--output-dir", default="/output", help="Directory for output files")
    parser.add_argument("--batch", type=int, default=20,
                        help="Number of issues per batch (default: 20)")
    parser.add_argument("--images", action="store_true",
                        help="Also generate article images CSVs")
    args = parser.parse_args()

    journal_url = f"{args.base_url.rstrip('/')}/{args.journal_path.strip('/')}"
    os.makedirs(args.output_dir, exist_ok=True)

    print("Fetching all published issues...")
    issues = fetch_all_issues(journal_url, args.api_key)
    issues_sorted = sorted(issues, key=lambda x: (x.get("year") or 0, x.get("id", 0)))
    total_issues = len(issues_sorted)
    total_batches = (total_issues + args.batch - 1) // args.batch
    print(f"  Found {total_issues} issue(s) — splitting into {total_batches} batch(es) of up to {args.batch}")

    html_warnings = []

    for batch_num in range(1, total_batches + 1):
        batch_issues = issues_sorted[(batch_num - 1) * args.batch: batch_num * args.batch]
        print(f"\n--- Batch {batch_num}/{total_batches} ---")

        all_rows = []
        image_rows = []

        for issue in batch_issues:
            issue_label = f"Vol. {issue.get('volume')} No. {issue.get('number')} ({issue.get('year', '')})"
            print(f"  {issue_label} (ID {issue['id']})...")

            section_cache = build_section_cache(journal_url, args.api_key, issue["id"], args.locale)
            submissions = fetch_submissions_for_issue(journal_url, args.api_key, issue["id"])
            print(f"    {len(submissions)} submission(s)")

            for i, sub in enumerate(submissions, 1):
                pub_stub = (sub.get("publications") or [{}])[-1]
                title_preview = get_locale_value(
                    pub_stub.get("fullTitle") or pub_stub.get("title"), args.locale
                )[:60] or f"submission {sub['id']}"
                print(f"    [{i}/{len(submissions)}] {title_preview}...")

                rows, doi, cover_image_url = submission_to_rows(
                    journal_url, args.base_url, args.api_key,
                    sub, issue, args.journal_code, args.locale, args.context_id,
                    section_cache,
                    get_current_publication,
                    get_pdf_url,
                    get_html_url,
                    get_cover_image_url,
                )
                all_rows.extend(rows)
                if cover_image_url and doi:
                    image_rows.append({"Identifier Type": "doi", "Identifier": doi, "URL": cover_image_url})

        articles_path = os.path.join(args.output_dir, f"janeway_articles_batch{batch_num:02d}.csv")
        write_article_csv(all_rows, articles_path)
        print(f"  Written: {articles_path} ({len(all_rows)} row(s))")

        if args.images:
            image_rows_with_images = [r for r in image_rows if r["URL"]]
            if image_rows_with_images:
                images_path = os.path.join(args.output_dir, f"janeway_images_batch{batch_num:02d}.csv")
                write_images_csv(image_rows_with_images, images_path)
                print(f"  Written: {images_path} ({len(image_rows_with_images)} article(s))")

    print(f"\nAll done. {total_batches} batch file(s) written to {args.output_dir}/")
    print("Upload each via Janeway > Manager > Plugins > Import Plugin > Article Import, Export, Update")

if __name__ == "__main__":
    main()