#!/usr/bin/python3
# @name: janeway_csv.py
# @creation_date: 2026-05-01
# @license: The MIT License <https://opensource.org/licenses/MIT>
# @author: Simon Bowie <simonxix@simonxix.com>
# @purpose: transforms OJS API data into the format required by the Janeway Imports plugin
# @acknowledgements:
# https://github.com/openlibhums/imports 
# https://janeway-imports.readthedocs.io/en/latest/index.html

import csv
import re
import sys
from datetime import datetime

from ojs_api import get_locale_value

############################################################
# data normalisation
############################################################

LOCALE_TO_ISO3 = {
    "en": "eng", "en_US": "eng", "en_GB": "eng",
    "fr": "fra", "fr_FR": "fra", "fr_CA": "fra",
    "de": "deu", "de_DE": "deu",
    "es": "spa", "es_ES": "spa",
    "pt": "por", "pt_PT": "por", "pt_BR": "por",
    "it": "ita", "it_IT": "ita",
    "nl": "nld", "nl_NL": "nld",
    "sv": "swe", "sv_SE": "swe",
    "no": "nor", "nb": "nor", "nb_NO": "nor",
    "da": "dan", "da_DK": "dan",
    "fi": "fin", "fi_FI": "fin",
    "pl": "pol", "pl_PL": "pol",
    "cs": "ces", "cs_CZ": "ces",
    "sk": "slk", "sk_SK": "slk",
    "hu": "hun", "hu_HU": "hun",
    "ro": "ron", "ro_RO": "ron",
    "bg": "bul", "bg_BG": "bul",
    "hr": "hrv", "hr_HR": "hrv",
    "sr": "srp", "sr_RS": "srp",
    "uk": "ukr", "uk_UA": "ukr",
    "ru": "rus", "ru_RU": "rus",
    "tr": "tur", "tr_TR": "tur",
    "ar": "ara", "ar_IQ": "ara",
    "zh": "zho", "zh_CN": "zho", "zh_TW": "zho",
    "ja": "jpn", "ja_JP": "jpn",
    "ko": "kor", "ko_KR": "kor",
    "fa": "fas", "fa_IR": "fas",
    "id": "ind", "id_ID": "ind",
    "ms": "msa", "ms_MY": "msa",
    "vi": "vie", "vi_VN": "vie",
    "ca": "cat", "ca_ES": "cat",
    "eu": "eus", "eu_ES": "eus",
    "gl": "glg", "gl_ES": "glg",
    "el": "ell", "el_GR": "ell",
    "he": "heb", "he_IL": "heb",
}

LICENCE_URL_TO_SHORT = {
    "https://creativecommons.org/licenses/by/4.0":        "CC BY 4.0",
    "https://creativecommons.org/licenses/by/4.0/":       "CC BY 4.0",
    "https://creativecommons.org/licenses/by/3.0":        "CC BY 3.0",
    "https://creativecommons.org/licenses/by/3.0/":       "CC BY 3.0",
    "https://creativecommons.org/licenses/by-sa/4.0":     "CC BY-SA 4.0",
    "https://creativecommons.org/licenses/by-sa/4.0/":    "CC BY-SA 4.0",
    "https://creativecommons.org/licenses/by-nc/4.0":     "CC BY-NC 4.0",
    "https://creativecommons.org/licenses/by-nc/4.0/":    "CC BY-NC 4.0",
    "https://creativecommons.org/licenses/by-nd/4.0":     "CC BY-ND 4.0",
    "https://creativecommons.org/licenses/by-nd/4.0/":    "CC BY-ND 4.0",
    "https://creativecommons.org/licenses/by-nc-sa/4.0":  "CC BY-NC-SA",
    "https://creativecommons.org/licenses/by-nc-sa/4.0/": "CC BY-NC-SA",
    "https://creativecommons.org/licenses/by-nc-nd/4.0":  "CC BY-NC-ND",
    "https://creativecommons.org/licenses/by-nc-nd/4.0/": "CC BY-NC-ND",
    "https://creativecommons.org/publicdomain/zero/1.0":  "CC0 1.0",
    "https://creativecommons.org/publicdomain/zero/1.0/": "CC0 1.0",
}

def locale_to_iso3(locale: str) -> str:
    if not locale:
        return "eng"
    if locale in LOCALE_TO_ISO3:
        return LOCALE_TO_ISO3[locale]
    if len(locale) == 3 and locale.isalpha():
        return locale.lower()
    return LOCALE_TO_ISO3.get(locale.split("_")[0], locale)

def normalise_doi(doi: str) -> str:
    if not doi:
        return ""
    doi = doi.strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.lower().startswith(prefix):
            doi = doi[len(prefix):]
    return doi if doi.startswith("10.") else ""

def normalise_date(date_str: str) -> str:
    if not date_str:
        return ""
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%m/%d/%Y", "%Y"):
        try:
            return datetime.strptime(date_str[:len(fmt)], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str[:10]

def normalise_licence(url: str) -> str:
    if not url:
        return ""
    url = url.strip().rstrip("/")
    for key, short in LICENCE_URL_TO_SHORT.items():
        if url == key.rstrip("/"):
            return short
    return url[:15] if len(url) > 15 else url

def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()

def split_full_name(full_name: str) -> tuple:
    """Split a display name into (salutation, first, middle, last)."""
    salutations = {"dr", "prof", "professor", "mr", "mrs", "ms", "mx", "rev"}
    parts = full_name.strip().split()
    salutation = ""
    if parts and parts[0].lower().rstrip(".") in salutations:
        salutation = parts.pop(0)
    if not parts:
        return salutation, "", "", ""
    if len(parts) == 1:
        return salutation, parts[0], "", ""
    if len(parts) == 2:
        return salutation, parts[0], "", parts[1]
    return salutation, parts[0], " ".join(parts[1:-1]), parts[-1]

############################################################
# article import CSV
############################################################

JANEWAY_COLUMNS = [
    "Janeway ID", "Article title", "Article abstract", "Keywords",
    "Rights", "Licence", "Language", "Peer reviewed (Y/N)",
    "Author salutation", "Author given name", "Author middle name",
    "Author surname", "Author suffix", "Author email", "Author ORCID",
    "Author institution", "Author department", "Author biography",
    "Author is primary (Y/N)", "Author is corporate (Y/N)",
    "DOI", "DOI (URL form)", "Date accepted", "Date published",
    "Article number", "First page", "Last page", "Page numbers (custom)",
    "Competing interests", "Article section", "Stage", "File import identifier",
    "Journal code", "Journal title override", "ISSN override",
    "Volume number", "Issue number", "Issue title", "Issue pub date", "PDF URI",
]

ARTICLE_LEVEL_FIELDS = (
    "Article title", "Article abstract", "Keywords", "Rights", "Licence",
    "DOI", "Date accepted", "Date published", "First page", "Last page",
    "Page numbers (custom)", "Article section", "PDF URI", "Stage",
    "Peer reviewed (Y/N)", "Volume number", "Issue number", "Issue title",
    "Issue pub date",
)

def empty_article_row(journal_code: str, issue: dict, locale: str) -> dict:
    return {col: "" for col in JANEWAY_COLUMNS} | {
        "Journal code": journal_code,
        "Volume number": str(issue.get("volume") or "0"),
        "Issue number": str(issue.get("number") or "0"),
        "Issue title": get_locale_value(issue.get("title"), locale),
        "Issue pub date": normalise_date(issue.get("datePublished", "")),
        "Stage": "Published",
        "Peer reviewed (Y/N)": "Y",
        "Language": locale_to_iso3(locale),
    }

def submission_to_rows(journal_url: str, site_base_url: str, api_key: str,
                       submission: dict, issue: dict, journal_code: str,
                       locale: str, context_id: str,
                       section_cache: dict,
                       get_current_publication_fn,
                       get_pdf_url_fn,
                       get_cover_image_url_fn) -> tuple:
    """Convert a single OJS submission into Janeway CSV rows.

    Returns (rows, doi, cover_image_url).
    One row per author; article-level fields only on first row.
    """
    pub = get_current_publication_fn(submission, api_key)
    if not pub:
        print(f"  Warning: no publication found for submission {submission['id']}", file=sys.stderr)
        return [], "", ""

    title = get_locale_value(pub.get("fullTitle") or pub.get("title"), locale)
    abstract = strip_html(get_locale_value(pub.get("abstract"), locale))

    kw_raw = pub.get("keywords") or {}
    kw_list = kw_raw.get(locale) or next(iter(kw_raw.values()), []) \
        if isinstance(kw_raw, dict) else kw_raw
    keywords = ", ".join(kw_list) if isinstance(kw_list, list) else str(kw_list)

    doi = normalise_doi((pub.get("doiObject") or {}).get("doi") or "")
    date_published = normalise_date(pub.get("datePublished", ""))
    licence = normalise_licence(pub.get("licenseUrl", ""))
    rights = get_locale_value(pub.get("rights"), locale)
    section_title = section_cache.get(pub.get("sectionId"), "")

    pages = pub.get("pages", "") or ""
    first_page = last_page = custom_pages = ""
    if pages:
        for sep in ("–", "-"):
            if sep in pages:
                parts = pages.split(sep, 1)
                first_page, last_page = parts[0].strip(), parts[1].strip()
                break
        else:
            custom_pages = pages

    pdf_uri = get_pdf_url_fn(journal_url, pub)
    cover_image_url = get_cover_image_url_fn(site_base_url, pub, context_id)

    base = empty_article_row(journal_code, issue, locale) | {
        "Article title": title,
        "Article abstract": abstract,
        "Keywords": keywords,
        "Rights": rights,
        "Licence": licence,
        "DOI": doi,
        "Date published": date_published,
        "First page": first_page,
        "Last page": last_page,
        "Page numbers (custom)": custom_pages,
        "Article section": section_title,
        "PDF URI": pdf_uri,
    }

    authors = pub.get("authors") or []
    if not authors:
        return [base], doi, cover_image_url

    primary_id = pub.get("primaryContactId")
    rows = []
    for i, author in enumerate(authors):
        row = dict(base)
        row["Author given name"] = get_locale_value(author.get("givenName"), locale).strip()
        row["Author middle name"] = ""
        row["Author surname"] = get_locale_value(author.get("familyName"), locale).strip()
        row["Author email"] = author.get("email", "")
        row["Author ORCID"] = author.get("orcid") or ""
        row["Author institution"] = get_locale_value(author.get("affiliation"), locale).strip()
        row["Author biography"] = strip_html(get_locale_value(author.get("biography"), locale))
        row["Author is primary (Y/N)"] = "Y" if (
            author.get("id") == primary_id if primary_id else i == 0
        ) else "N"
        row["Author is corporate (Y/N)"] = "N"

        if i > 0:
            for field in ARTICLE_LEVEL_FIELDS:
                row[field] = ""

        rows.append(row)

    return rows, doi, cover_image_url

def write_article_csv(rows: list, path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=JANEWAY_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

############################################################
# article images CSV
############################################################

IMAGES_COLUMNS = ["Identifier Type", "Identifier", "URL"]

def write_images_csv(rows: list, path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=IMAGES_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

############################################################
# editorial team CSV
############################################################

EDITORIAL_TEAM_COLUMNS = [
    "Salutation", "firstname", "middlename", "lastname",
    "email_address", "department", "institution", "country", "group name",
]

def editorial_users_to_rows(users_and_groups: list, locale: str) -> list:
    rows = []
    for user, groups in users_and_groups:
        salutation, first, middle, last = split_full_name(user.get("fullName", ""))
        for group in groups:
            rows.append({
                "Salutation": salutation,
                "firstname": first,
                "middlename": middle,
                "lastname": last,
                "email_address": user.get("email", ""),
                "department": "",
                "institution": get_locale_value(user.get("affiliation"), locale).strip(),
                "country": user.get("country", ""),
                "group name": get_locale_value(group.get("name"), locale),
            })
    return rows

def write_editorial_csv(rows: list, path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EDITORIAL_TEAM_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

############################################################
# editors CSV
############################################################

EDITORS_COLUMNS = [
    "salutation", "firstname", "middlename", "lastname",
    "email_address", "department", "institution", "country",
]

def write_editors_csv(users_and_groups: list, path: str, locale: str) -> int:
    seen = set()
    rows = []
    for user, _groups in users_and_groups:
        if user["id"] in seen:
            continue
        seen.add(user["id"])
        salutation, first, middle, last = split_full_name(user.get("fullName", ""))
        rows.append({
            "salutation": salutation,
            "firstname": first,
            "middlename": middle,
            "lastname": last,
            "email_address": user.get("email", ""),
            "department": "",
            "institution": get_locale_value(user.get("affiliation"), locale).strip(),
            "country": user.get("country", ""),
        })
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EDITORS_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)

############################################################
# reviewers CSV
############################################################

REVIEWERS_COLUMNS = [
    "salutation", "firstname", "middlename", "lastname",
    "email_address", "department", "institution", "country", "interests",
]

def write_reviewers_csv(users: list, path: str, locale: str) -> int:
    rows = []
    for user in users:
        salutation, first, middle, last = split_full_name(user.get("fullName", ""))
        interests = "; ".join(
            i.get("interest", "") for i in (user.get("interests") or [])
            if i.get("interest")
        )
        rows.append({
            "salutation": salutation,
            "firstname": first,
            "middlename": middle,
            "lastname": last,
            "email_address": user.get("email", ""),
            "department": "",
            "institution": get_locale_value(user.get("affiliation"), locale).strip(),
            "country": user.get("country", ""),
            "interests": interests,
        })
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEWERS_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)
