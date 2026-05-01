#!/usr/bin/python3
# @name: ojs_api.py
# @creation_date: 2026-05-01
# @license: The MIT License <https://opensource.org/licenses/MIT>
# @author: Simon Bowie <simonxix@simonxix.com>
# @purpose: performs authentication and data fetching from an OJS 3.4 REST API
# @acknowledgements:
# https://docs.pkp.sfu.ca/dev/api/ojs/3.4

import json
import sys
import urllib.error
import urllib.parse
import urllib.request

############################################################
# HTTP helpers
############################################################

def api_get(journal_url: str, path: str, api_key: str, params: dict = None) -> dict:
    """Make an authenticated GET request to the OJS REST API."""
    all_params = dict(params or {})
    all_params["apiToken"] = api_key
    url = f"{journal_url.rstrip('/')}/api/v1/{path.lstrip('/')}?{urllib.parse.urlencode(all_params)}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "ojs-to-janeway/1.0",
    })
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code} for {url}: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection error for {url}: {e.reason}", file=sys.stderr)
        sys.exit(1)

def api_get_href(href: str, api_key: str) -> dict:
    """Fetch a full URL (from _href fields) with apiToken appended."""
    sep = "&" if "?" in href else "?"
    url = f"{href}{sep}apiToken={urllib.parse.quote(api_key)}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "ojs-to-janeway/1.0",
    })
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  Warning: HTTP {e.code} fetching {href}: {body}", file=sys.stderr)
        return {}
    except urllib.error.URLError as e:
        print(f"  Warning: connection error fetching {href}: {e.reason}", file=sys.stderr)
        return {}

def paginate(journal_url: str, path: str, api_key: str, params: dict = None) -> list:
    """Fetch all pages of a paginated OJS API endpoint."""
    params = dict(params or {})
    params.setdefault("count", 100)
    params["offset"] = 0
    results = []
    while True:
        page = api_get(journal_url, path, api_key, params)
        items = page.get("items", [])
        results.extend(items)
        if len(results) >= page.get("itemsMax", 0):
            break
        params["offset"] += len(items)
        if not items:
            break
    return results

############################################################
# locale helper
############################################################

def get_locale_value(field, locale: str = "en") -> str:
    """Extract a value from an OJS locale dict, falling back to first available."""
    if not field:
        return ""
    if isinstance(field, str):
        return field
    if isinstance(field, dict):
        for key in (locale, "en", "en_US", "en_GB"):
            if field.get(key):
                return field[key]
        for v in field.values():
            if v:
                return v
    return ""

############################################################
# issue fetching
############################################################

def fetch_issue(journal_url: str, api_key: str, issue_id: int) -> dict:
    return api_get(journal_url, f"issues/{issue_id}", api_key)


def fetch_all_issues(journal_url: str, api_key: str) -> list:
    return paginate(journal_url, "issues", api_key, {"isPublished": 1})


def fetch_submissions_for_issue(journal_url: str, api_key: str, issue_id: int) -> list:
    return paginate(journal_url, "submissions", api_key, {
        "issueIds": issue_id,
        "status": 3,
    })

def build_section_cache(journal_url: str, api_key: str, issue_id: int, locale: str) -> dict:
    """Return {section_id: section_title} from the issue TOC.

    The /sections endpoint does not exist in OJS 3.4; titles come from
    the issue object's sections[] array.
    """
    issue = api_get(journal_url, f"issues/{issue_id}", api_key)
    cache = {}
    for section in (issue.get("sections") or []):
        sid = section.get("id")
        if sid:
            cache[sid] = get_locale_value(section.get("title"), locale)
    return cache

############################################################
# publication fetching
############################################################

def get_current_publication(submission: dict, api_key: str) -> dict:
    """Fetch the full current publication object for a submission.

    The submissions list endpoint returns publications[] with partial data;
    we fetch the full object via _href to get abstract, keywords, authors etc.
    """
    pubs = submission.get("publications") or []
    if not pubs:
        return {}
    current_id = submission.get("currentPublicationId")
    pub_stub = next((p for p in pubs if p.get("id") == current_id), pubs[-1]) \
        if current_id else pubs[-1]
    href = pub_stub.get("_href")
    return api_get_href(href, api_key) if href else pub_stub

def get_pdf_url(journal_url: str, pub: dict) -> str:
    """Build a direct PDF download URL using the OJS article/download endpoint.

    Pattern: {journal_url}/article/download/{submissionId}/{galleyId}
    Returns application/pdf without authentication.
    """
    submission_id = pub.get("submissionId")
    for galley in (pub.get("galleys") or []):
        if "PDF" in (galley.get("label") or "").upper():
            galley_id = galley.get("id")
            if submission_id and galley_id:
                return f"{journal_url.rstrip('/')}/article/download/{submission_id}/{galley_id}"
    return ""

def get_cover_image_url(site_base_url: str, pub: dict, context_id: str) -> str:
    """Build the public URL for an OJS article cover image.

    Pattern: {site_base_url}/public/journals/{contextId}/{uploadName}
    Note: uses site root, not journal path.
    """
    cover = pub.get("coverImage") or {}
    for locale_data in cover.values():
        upload_name = (locale_data or {}).get("uploadName")
        if upload_name and context_id:
            return f"{site_base_url.rstrip('/')}/public/journals/{context_id}/{upload_name}"
    return ""

def detect_context_id(journal_url: str, api_key: str, issues: list) -> str | None:
    """Try to detect the OJS journal context ID from doiObject.contextId."""
    for issue in issues:
        subs = paginate(journal_url, "submissions", api_key, {
            "issueIds": issue["id"], "status": 3, "count": 1
        })
        for sub in subs:
            pub_stub = (sub.get("publications") or [{}])[-1]
            href = pub_stub.get("_href")
            if href:
                pub = api_get_href(href, api_key)
                context_id = (pub.get("doiObject") or {}).get("contextId")
                if context_id:
                    return str(context_id)
    return None

############################################################
# user fetching
############################################################

# OJS role IDs considered editorial (excludes Reviewer=4096, Author=65536,
# Reader=1048576, Subscription Manager=2097152)
EDITORIAL_ROLE_IDS = {16, 17, 4097}
REVIEWER_ROLE_ID = 4096

def fetch_editorial_users(journal_url: str, api_key: str) -> list:
    """Fetch all users with at least one editorial role.

    Returns list of (user, editorial_groups) tuples.
    """
    all_users = paginate(journal_url, "users", api_key)
    return [
        (user, [g for g in (user.get("groups") or []) if g.get("roleId") in EDITORIAL_ROLE_IDS])
        for user in all_users
        if any(g.get("roleId") in EDITORIAL_ROLE_IDS for g in (user.get("groups") or []))
    ]

def fetch_reviewer_users(journal_url: str, api_key: str) -> list:
    """Fetch all users with the Reviewer role (roleId 4096)."""
    return paginate(journal_url, "users", api_key, {"roleIds": REVIEWER_ROLE_ID})
