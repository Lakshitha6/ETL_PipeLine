from datetime import datetime, timezone

from database.client import get_db_client

DB_NAME = "job_aggregator"
COLLECTION_NAME = "jobs"

def setup_ttl_index(client):
    """
    Creates a TTL index on 'last_seen' to auto-delete jobs after 48 hours.
    """
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    
    # 48 hours = 48 * 60 * 60 = 172800 seconds
    collection.create_index(
        [("last_seen", 1)], 
        expireAfterSeconds=172800,
        name="last_seen_ttl_48h"
    )
    print("TTL index verified/created for 48-hour auto-deletion.")


def upsert_jobs(jobs: list):
    """
    Inserts new jobs or updates the 'last_seen' timestamp of existing jobs.
    """
    if not jobs:
        print("No jobs to upsert.")
        return

    client = get_db_client()
    if not client:
        return

    try:
        setup_ttl_index(client)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        now = datetime.now(timezone.utc)
        inserted_count = 0
        updated_count = 0

        for job in jobs:
            # The unique identifier for a job is its source + external_id
            filter_query = {
                "source": job["source"],
                "external_id": job["external_id"]
            }
            
            # $setOnInsert ensures first_seen is only set once when the job is brand new
            # $set updates the entire job doc and refreshes last_seen so it doesn't get deleted
            update_query = {
                "$set": {**job, "last_seen": now},
                "$setOnInsert": {"first_seen": now}
            }
            
            result = collection.update_one(filter_query, update_query, upsert=True)
            
            if result.upserted_id:
                inserted_count += 1
            elif result.modified_count > 0:
                updated_count += 1

        print(f"Database Pipeline complete: {inserted_count} new jobs inserted, {updated_count} existing jobs updated.")
        
    except Exception as e:
        print(f"Database Error during upsert: {e}")
    finally:
        client.close()