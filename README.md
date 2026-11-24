# Job Finding ETL Pipeline

A Python ETL pipeline that collects Sri Lankan job listings from multiple sources, cleans and enriches each listing, and stores the results in MongoDB.

The pipeline combines jobs from:

- Rooster.jobs - Scrape the website
- ITPro.lk - Call the API
- Jobseeker.lk - Scrape the website

![alt text](ETL_Image.jfif)

## Features

- Extracts listings from three different job sources
- Converts source-specific fields into a consistent job format
- Normalizes job types and missing values
- Extracts a predefined set of technology skills from job titles and descriptions
- Converts ITPro.lk HTML descriptions into Markdown
- Uses MongoDB upserts to avoid duplicate source/job combinations
- Tracks `first_seen` and refreshes `last_seen` for recurring listings
- Automatically removes listings that have not been seen for 48 hours

## How It Works

### 1. Extract

`main.py` collects raw job records:

- Rooster.jobs: 50 listings
- ITPro.lk: 50 listings
- Jobseeker.lk: 5 pages

The individual scrapers handle failed HTTP requests and return an empty list or partial results when possible.

### 2. Transform

`processors/cleaner.py` standardizes fields and fills common defaults:

- Untitled listings become `"Untitled Role"`
- Unknown company names become `"Not specified"` or an employer-specific fallback
- Unknown locations default to `"Sri Lanka"`
- Job types are normalized to `Internship`, `Part-time`, `Contract`, `Full-time`, or `Not specified`
- Descriptions are limited to 2,500 characters
- Technology keywords found in the title or description are added to `extracted_skills`

### 3. Load

`database/operations.py` stores jobs in MongoDB using a compound identity of:

```text
source + external_id
```

New records receive `first_seen` and `last_seen` timestamps. Existing records are updated and their `last_seen` timestamp is refreshed. A TTL index deletes records that have not been seen for 48 hours.

## Data Sources

| Source | Method | Identifier |
| --- | --- | --- |
| Rooster.jobs | REST API | Rooster job ID |
| ITPro.lk | REST API | ITPro job ID |
| Jobseeker.lk | HTML scraping | Canonical job URL |

Scraping depends on the structure and availability of external websites and APIs.

## MongoDB Document Shape

```json
{
  "source": "Jobseeker.lk",
  "external_id": "https://jobseeker.lk/example-job/",
  "title": "Python Developer",
  "company": "Example Company",
  "logo": "",
  "url": "https://jobseeker.lk/example-job/",
  "location": "Sri Lanka",
  "job_type": "Full-time",
  "salary": "Not specified",
  "category": "IT Jobs",
  "deadline": "2026-12-31",
  "description": "Job listing description",
  "posted_at": null,
  "scraped_at": "2026-11-24T16:25:23+00:00",
  "extracted_skills": ["Python", "SQL"],
  "first_seen": "2026-11-24T16:25:23+00:00",
  "last_seen": "2026-11-24T16:25:23+00:00"
}
```

Database name: `job_aggregator`

Collection name: `jobs`

TTL field: `last_seen`

Retention period: 48 hours

## Requirements

- Python 3.10 or newer
- MongoDB or MongoDB Atlas
- Internet access for the external job sources

## Installation

### 1. Clone the repository

```powershell
git clone https://github.com/Lakshitha6/ETL_PipeLine.git
cd ETL_PipeLine
```

### 2. Create a virtual environment

Using `venv`:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

Using `uv`:

```powershell
uv sync
```

### 3. Install dependencies

For a standard Python environment:

```powershell
pip install -r requirements.txt
```

For a `uv` environment, dependency installation is handled with:

```powershell
uv sync
```

## Configuration

Create a `.env` file in the project root:

```env
MONGO_URI=mongodb://localhost:27017
```

For MongoDB Atlas, use the connection string generated for your database cluster:

```env
MONGO_URI=mongodb+srv://<username>:<password>@<cluster-host>/<database>
```

Do not commit `.env` or MongoDB credentials to source control.

## Running the Pipeline

Run the main entry point:

```powershell
python main.py
```

Successful execution prints extraction, cleaning, database, and completion information. If no jobs are extracted, the pipeline exits with status code `1`.

## Testing Scrapers

The repository includes `test_scrapers.py` as a full pipeline smoke test:

```powershell
python test_scrapers.py
```

This test extracts a smaller Jobseeker.lk page range (3 pages), cleans all results, and performs MongoDB upserts.

## Project Structure

```text
ETL_Pipeline/
├── main.py                 # ETL entry point
├── test_scrapers.py        # Manual end-to-end pipeline test
├── pyproject.toml          # Project and dependency metadata
├── requirements.txt        # Exported package dependencies
├── uv.lock                 # uv dependency lock file
├── scrapers/
│   ├── rooster.py          # Rooster.jobs API scraper
│   ├── itpro.py            # ITPro.lk API scraper
│   └── jobseeker.py        # Jobseeker.lk HTML scraper
├── processors/
│   └── cleaner.py          # Cleaning and skill extraction
├── database/
│   ├── client.py           # MongoDB connection
│   └── operations.py       # Upserts and TTL setup
└── config/                 # Reserved for future configuration modules
```

## Extracted Skills

The cleaner searches for a fixed set of technologies, including:

- Languages: Python, JavaScript, TypeScript, Java, C++, C#, Go, Rust, PHP
- Frameworks: React, Next.js, Vue, Angular, Node.js, Django, Flask, FastAPI
- Databases: MongoDB, PostgreSQL, MySQL, Redis, Firebase, SQLite, SQL
- Cloud and DevOps: Docker, Kubernetes, AWS, Azure, GCP, CI/CD, Git
- Data and AI: Machine Learning, NLP, Data Science, TensorFlow, PyTorch
- Testing: QA, Quality Assurance, Testing

## Troubleshooting

### `MONGO_URI is not set`

Make sure `.env` exists in the project root and contains a valid `MONGO_URI`.

### MongoDB connection failure

- Check that MongoDB is running.
- Verify the host, port, username, password, and database URL.
- Allow the MongoDB host through local or network firewalls.

### No jobs extracted

The external APIs or website may be unavailable, or network access may be blocked. The scraper functions print source-specific errors to the console.

## License

No license has been specified for this repository.