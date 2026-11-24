TECH_SKILLS = {
    "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust",
    "react", "next.js", "vue", "angular", "svelte", "node.js", "express",
    "html", "css", "tailwind", "bootstrap",
    "mongodb", "postgresql", "mysql", "redis", "firebase", "sqlite", "sql",
    "docker", "kubernetes", "aws", "azure", "gcp", "ci/cd", "git", "github",
    "machine learning", "nlp", "data science", "tensorflow", "pytorch",
    "scrapy", "beautifulsoup", "selenium", "playwright", "fastapi", "django", "flask",
    "php", "laravel", "wordpress", "shopify", "qa", "quality assurance", "testing"
}


def clean_and_enrich_job(job: dict) -> dict:
    """
    Takes a raw job dictionary from any scraper, cleans nulls, normalizes fields, 
    and enriches it with extracted NLP skills.
    """

    # Normalize None/Empty values
    title = (job.get("title") or "Untitled Role").strip()
    company = (job.get("company") or "Not specified").strip()
    location = (job.get("location") or "Sri Lanka").strip() # Default to Sri Lanka
    salary = (job.get("salary") or "Not specified").strip()
    description = (job.get("description") or "").strip()

    # Ensure external_id is always a string for consistent MongoDB indexing
    external_id = str(job.get("external_id", "")).strip()

    # Normalize Job variations like "Intern", "full-time" etc.

    job_type_raw = str(job.get("job_type") or "").lower().strip()
    if any(x in job_type_raw for x in ["intern", "trainee"]):
        job_type = "Internship"
    elif any(x in job_type_raw for x in ["part-time", "part time"]):
        job_type = "Part-time"
    elif any(x in job_type_raw for x in ["contract", "freelance"]):
        job_type = "Contract"
    elif any(x in job_type_raw for x in ["full-time", "full time", "permanent"]):
        job_type = "Full-time"
    else:
        job_type = job_type_raw if job_type_raw and not job_type_raw.isdigit() else "Not specified"

    # Combine title and description for a richer text body to search
    text_body = f"{title} {description}".lower()
    
    extracted_skills = []
    for skill in TECH_SKILLS:
        if skill in text_body:
            extracted_skills.append(skill.title())

    clean_job = {
        "source": job.get("source", "Unknown"),
        "external_id": external_id,
        "title": title,
        "company": company,
        "logo": job.get("logo") or "", # Empty string instead of None for React <img> tags
        "url": job.get("url", ""),
        "location": location,
        "job_type": job_type,
        "salary": salary,
        "category": job.get("category") or "General", # From Jobseeker
        "deadline": job.get("deadline"),              # From Jobseeker
        "description": description[:2500],            # Truncate huge descriptions to save DB space & API payload
        "posted_at": job.get("posted_at"),
        "scraped_at": job.get("scraped_at"),
        "extracted_skills": list(set(extracted_skills)), # Remove duplicates
    }
    
    return clean_job


def process_all_jobs(raw_jobs: list) -> list:
    """
    Processes a list of raw jobs from any combination of scrapers.
    """
    cleaned_jobs = []
    for job in raw_jobs:
        try:
            cleaned_job = clean_and_enrich_job(job)
            cleaned_jobs.append(cleaned_job)
        except Exception as e:
            print(f"Cleaner Error processing job '{job.get('title')}': {e}")
            
    print(f"Cleaner Successfully cleaned and enriched {len(cleaned_jobs)} jobs.")
    return cleaned_jobs