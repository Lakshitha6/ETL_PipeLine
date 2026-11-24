import sys
from scrapers.rooster import scrape_rooster
from scrapers.itpro import scrape_itpro
from scrapers.jobseeker import scrape_jobseeker
from processors.cleaner import process_all_jobs
from database.operations import upsert_jobs

def main():
    print("="*60)
    print("Starting Job Aggregator ETL Pipeline")
    print("="*60)

    # 1. EXTRACT
    print("\n Extracting data from sources...")
    raw_jobs = []
    
    raw_jobs.extend(scrape_rooster(limit=50))
    raw_jobs.extend(scrape_itpro(limit=50))
    raw_jobs.extend(scrape_jobseeker(pages=5))
    
    if not raw_jobs:
        print("No jobs extracted. Exiting pipeline.")
        sys.exit(1)

    print(f"Extracted {len(raw_jobs)} raw jobs.")

    # 2. TRANSFORM
    print("\n Cleaning and enriching data...")
    cleaned_jobs = process_all_jobs(raw_jobs)

    # 3. LOAD
    print("\n Loading data into MongoDB...")
    upsert_jobs(cleaned_jobs)

    print("\n" + "="*60)
    print("ETL Pipeline finished successfully!")
    print("="*60)

if __name__ == "__main__":
    main()