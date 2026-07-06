import os
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

def init_dataset():
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project:
        print("❌ GOOGLE_CLOUD_PROJECT not found in .env")
        return

    # Assuming service-account.json is present and implicitly used or GOOGLE_APPLICATION_CREDENTIALS is set
    # Wait, the code doesn't explicitly set GOOGLE_APPLICATION_CREDENTIALS in .env in our instructions.
    # Let's explicitly point to it if it exists.
    sa_path = os.path.join(os.path.dirname(__file__), "service-account.json")
    if os.path.exists(sa_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = sa_path
        print("✅ Found service-account.json")

    client = bigquery.Client(project=project)
    dataset_id = f"{project}.jansetu_mvp"
    
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = "US"
    
    try:
        dataset = client.create_dataset(dataset, timeout=30)
        print(f"✅ Created BigQuery dataset: {dataset_id}")
    except Exception as e:
        if "Already Exists" in str(e) or "already exists" in str(e).lower():
            print(f"✅ Dataset {dataset_id} already exists.")
        else:
            print(f"❌ Error creating dataset: {e}")

if __name__ == "__main__":
    init_dataset()
