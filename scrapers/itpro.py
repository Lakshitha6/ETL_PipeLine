import requests
from datetime import datetime, timezone
import html2text


URL = "https://itpro.lk/api/v1/jobs"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
}

def scrape_itpro(limit=50):

    """Fetches and normalizes job listings from the ITPro.lk public API.

    Sends a GET request to the ITPro.lk jobs endpoint, converts HTML job
    descriptions into plain Markdown text (stripping links), and maps the
    first ``limit`` results into a standardized dictionary format. If the API
    request fails, it logs the error to stdout and returns an empty list.

    Args:
        limit (int, optional): The maximum number of job listings to process
            from the API response. Defaults to 50.

    Returns:
        list[dict]: A list of dictionaries where each dictionary represents a
        normalized job posting with the following keys:
            - source (str): Always `"ITPro.lk"`.
            - external_id (str): Unique job identifier from ITPro.
            - title (str): Job title.
            - company (str): Hiring company name (defaults to
              `"ITPro Employer"`).
            - logo (str): Always an empty string `""` (not provided by API).
            - url (str): Direct public URL to the job listing.
            - location (str): Raw numeric location ID as a string (e.g., `"79"`),
              or `"None"` if null.
            - job_type (str): Raw numeric job type ID as a string (e.g., `"1"`).
            - salary (str): Always `"Not specified"`.
            - description (str): Cleaned Markdown-formatted job description
              with hyperlinks removed.
            - posted_at (str | None): Timestamp string of when the job was
              posted (e.g., `"2026-11-23 19:42:25"`).
            - scraped_at (str): UTC ISO-8601 timestamp of when the scrape ran.
    """


    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"ITPro Error fetching jobs: {e}")
        return []

    jobs = []
    now = datetime.now(timezone.utc).isoformat()
    html_converter = html2text.HTML2Text()
    html_converter.ignore_links = True
    
    for j in data[:limit]:
        job_id = str(j.get("id"))
        loc_code = str(j.get("location", ""))
        type_code = str(j.get("type_id", ""))
        
        raw_desc = j.get("description", "")
        clean_desc = html_converter.handle(raw_desc).strip()

        jobs.append({
            "source": "ITPro.lk",
            "external_id": job_id,
            "title": (j.get("title") or "").strip(),
            "company": (j.get("company") or "ITPro Employer").strip(),
            "logo": "",
            "url": f'https://itpro.lk/jobs/{job_id}',
            "location":  loc_code,
            "job_type": type_code,
            "salary": "Not specified",
            "description": clean_desc,
            "posted_at": j.get("created_on"),
            "scraped_at": now,
        })
    
    print(f"ITPro Successfully scraped {len(jobs)} jobs.")
    return jobs