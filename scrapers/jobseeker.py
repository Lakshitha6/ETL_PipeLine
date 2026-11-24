import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from urllib.parse import urljoin

BASE_URL = "https://jobseeker.lk"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
}

session = requests.Session()
session.headers.update(HEADERS)


def parse_deadline(text):
    """Extracts and normalizes an application deadline date from job snippet text.

    Searches for patterns like ``Deadline:- 30th November 2026`` and converts
    the matched date into an ISO-8601 date string.

    Args:
        text (str): Raw text snippet from a job listing card.

    Returns:
        str | None: The deadline formatted as ``YYYY-MM-DD`` (e.g.,
        ``"2026-11-30"``), or ``None`` if no valid date pattern is found.
    """

        
    m = re.search(r"Deadline\s*:-?\s*(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(\d{4})", text)
    if not m:
        return None
    try:
        return datetime.strptime(f"{m[1]} {m[2]} {m[3]}", "%d %B %Y").date().isoformat()
    except ValueError:
        return None


def parse_company(text):
    """Heuristically extracts the hiring company name from a job snippet.

    Checks for explicit labels such as ``Company:- <Name>`` first, then falls
    back to common announcement prefixes like ``WE ARE HIRING | <Name>``,
    ``Join <Name>``, or ``at <Name>``.

    Args:
        text (str): Raw text snippet from a job listing card.

    Returns:
        str | None: The extracted company name, or ``None`` if no matching
        pattern is found.
    """

    # Primary pattern: "Company:- X"
    m = re.search(r"Company\s*:-?\s*(.+?)(?:\s+(?:Qualifications|Apply|Deadline|Location)\b|$)", text)
    if m:
        return m.group(1).strip()
    
    # Fallback pattern: "WE ARE HIRING | Company Name" or "Join [Company Name]"
    m2 = re.search(r"(?:WE ARE HIRING \| |Join |at )([A-Z][A-Za-z0-9\s&().,'-]+?)(?:\s+Location:|Location:|$)", text)
    if m2:
        return m2.group(1).strip()
        
    return None


def scrape_jobseeker(pages=1, delay=1.0):
    """Scrapes and normalizes job listings from Jobseeker.lk listing pages.

    Iterates through paginated HTML pages on Jobseeker.lk (typically ~18 jobs
    per page), parses `<article>` cards with BeautifulSoup, deduplicates entries
    by URL (including sidebar "You may have missed" cards), and maps them into
    a standardized dictionary format. Stops early and returns any jobs collected
    so far if a page request fails.

    Args:
        pages (int, optional): Number of listing pages to scrape starting from
            page 1. Defaults to 1.
        delay (float, optional): Seconds to sleep between consecutive page
            requests to avoid rate limiting. Defaults to 1.0.

    Returns:
        list[dict]: A list of dictionaries where each dictionary represents a
        normalized job posting with the following keys:
            - source (str): Always `"Jobseeker.lk"`.
            - external_id (str): Canonical job URL used as a unique ID.
            - title (str): Job title from the `<h3>` heading.
            - company (str | None): Parsed employer name, or ``None``.
            - logo (str | None): Thumbnail image URL if present, else ``None``.
            - url (str): Direct public URL to the job listing.
            - location (None): Always ``None`` (not parsed from listing cards).
            - job_type (None): Always ``None`` (not parsed from listing cards).
            - salary (None): Always ``None`` (not parsed from listing cards).
            - category (str | None): Comma-separated category tags (e.g.,
              `"Internship, IT Jobs"`), or ``None``.
            - deadline (str | None): ISO-8601 deadline date (`YYYY-MM-DD`),
              or ``None``.
            - description (str | None): Combined `<p>` snippet text from the
              listing card, or ``None``.
            - posted_at (None): Always ``None``.
            - scraped_at (str): UTC ISO-8601 timestamp truncated to seconds.
    """


    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    jobs, seen_urls = [], set()

    for page in range(1, pages + 1):
        page_url = BASE_URL if page == 1 else f"{BASE_URL}/page/{page}/"
        try:
            response = session.get(page_url, timeout=15)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Jobseeker Error fetching page {page}: {e}")
            break

        soup = BeautifulSoup(response.text, "lxml")

        for article in soup.find_all("article"):
            title_tag = article.select_one("h3 a")
            if not title_tag or not title_tag.get("href"):
                continue

            url = urljoin(BASE_URL, title_tag["href"])
            if url in seen_urls:
                continue
            seen_urls.add(url)

            snippet = " ".join(p.get_text(" ", strip=True) for p in article.find_all("p"))
            img = article.find("img")
            categories = [a.get_text(strip=True) for a in article.select("a[href*='/category/']")]

            jobs.append({
                "source": "Jobseeker.lk",
                "external_id": url,
                "title": title_tag.get_text(strip=True),
                "company": parse_company(snippet),
                "logo": img.get("src") if img else None,
                "url": url,
                "location": None,
                "job_type": None,
                "salary": None,
                "category": ", ".join(categories) or None,
                "deadline": parse_deadline(snippet),
                "description": snippet or None,
                "posted_at": None,
                "scraped_at": now,
            })

        if page < pages:
            time.sleep(delay)

    print(f"Jobseeker Successfully scraped {len(jobs)} jobs.")
    return jobs