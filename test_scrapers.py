from scrapers.rooster import scrape_rooster
from scrapers.itpro import scrape_itpro
from scrapers.jobseeker import scrape_jobseeker
from processors.cleaner import process_all_jobs
from database.operations import upsert_jobs

if __name__ == "__main__":
    print("--- 1. Extracting Raw Data ---")
    raw_jobs = []
    raw_jobs.extend(scrape_rooster(limit=50))
    raw_jobs.extend(scrape_itpro(limit=50))
    raw_jobs.extend(scrape_jobseeker(pages=3))
    
    print(f"\nTotal raw jobs extracted: {len(raw_jobs)}")
    
    print("\n--- 2. Transforming Data (Cleaning & NLP) ---")
    cleaned_jobs = process_all_jobs(raw_jobs)
    
    print("\n--- 3. Loading Data into MongoDB ---")
    upsert_jobs(cleaned_jobs)
    
    print("\n✅ Full ETL Pipeline test completed successfully!")