import requests
from datetime import datetime, timezone

URL = "https://api.rooster.jobs/jobSearch/jobs/search"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Origin": "https://rooster.jobs",
    "Referer": "https://rooster.jobs/",
}

def scrape_rooster(limit=50):

    """Fetches and normalizes job listings from the Rooster.jobs search API.

    Sends a POST request to the Rooster.jobs API to retrieve the latest job
    postings and maps them into a standardized dictionary format. If the API
    request fails, it logs the error to stdout and returns an empty list.

    Args:
        limit (int, optional): The maximum number of job listings to fetch
            in a single request. Defaults to 50.

    Returns:
        list[dict]: A list of dictionaries where each dictionary represents a
        normalized job posting with the following keys:
            - source (str): Always `"Rooster.jobs"`.
            - external_id (str): Unique job identifier from Rooster.
            - title (str): Job title.
            - company (str): Subsidiary or parent company name (defaults to
              `"Rooster Employer"`).
            - logo (str): URL to the company logo, or an empty string.
            - url (str): Direct public URL to the job listing.
            - location (str): Job location (defaults to `"Not specified"`).
            - job_type (str): Employment type (defaults to `"Not specified"`).
            - salary (str): Formatted salary range (e.g., `"LKR 50000-100000/month"`),
              or an empty string if undisclosed.
            - description (str): Raw job description text or HTML.
            - posted_at (str | None): ISO timestamp of when the job was created.
            - scraped_at (str): UTC ISO-8601 timestamp of when the scrape ran.
    """


    payload = {"query": [], "limit": limit, "page": 1, "filters": {}}

    try:
        response = requests.post(url=URL, json=payload, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json().get("body", {}).get("data", [])

    except requests.exceptions.RequestException as e:
        print(f"Rooster Error fetching jobs: {e}")
        return []

    jobs = []

    now = datetime.now(timezone.utc).isoformat()

    for job in data:
        company = job.get("subsidiary_company_name") or job.get("company_name") or "Rooster Employer"
        logo = job.get("subsidiary_company_logo_url") or job.get("company_logo_url") or ""

        salary = ""
        if job.get("min_salary") or job.get("max_salary"):
            currency = job.get("salary_currency", "LKR")
            freq = job.get("salary_frequency", "month")
            salary = f"{currency} {job.get('min_salary')}-{job.get('max_salary')}/{freq}"

        jobs.append({
            "source": "Rooster.jobs",
            "external_id": str(job["id"]),
            "title": (job.get("title") or "").strip(),
            "company": company.strip(),
            "logo": logo,
            "url": f'https://rooster.jobs/jobs/{job["id"]}',
            "location": job.get("location", "Not specified"),
            "job_type": job.get("job_type", "Not specified"),
            "salary": salary,
            "description": job.get("description", ""),
            "posted_at": job.get("created_at"),
            "scraped_at": now,
        })
    
    print(f"Rooster Successfully scraped {len(jobs)} jobs.")

    return jobs