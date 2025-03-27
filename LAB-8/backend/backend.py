from fastapi import FastAPI, Form
from elasticsearch import Elasticsearch
from time import sleep

app = FastAPI()

# Elasticsearch v8 settings
ELASTICSEARCH_HOST = "http://elasticsearch:9200"
ELASTIC_USERNAME = "elastic"
ELASTIC_PASSWORD = "backelastic"

# Connect to Elasticsearch with authentication & SSL disabled
def connect_elasticsearch(tries=6):
    es = None
    # while (es is None ) and (tries):
    while (es is None ):
        try:
            es = Elasticsearch(
                ELASTICSEARCH_HOST,
                basic_auth=(ELASTIC_USERNAME, ELASTIC_PASSWORD),
                verify_certs=False  # Disable SSL verification for testing
            )
            if es.ping():
                print("Connected to Elasticsearch!")
                # break
                return es
        except Exception as e:
            print("Waiting for Elasticsearch to start...", e)
            sleep(5)
        # tries = tries - 1
    print("Failed to connect to Elasticsearch after multiple attempts.")
    return None

# Establish Elasticsearch connection
print("Here1")
es = connect_elasticsearch()
if es is None:
    raise Exception("Elasticsearch is not available!")
else:
    INDEX_NAME = "documents"

    # Ensure index exists
    while True:
        try:
            if not es.indices.exists(index=INDEX_NAME):
                es.indices.create(index=INDEX_NAME, mappings={"properties": {"id": {"type": "keyword"}, "text": {"type": "text"}}})
                print(f"Created index: {INDEX_NAME}")
            break
        except Exception as e:
            print("Waiting for Elasticsearch index to be available...", e)
            sleep(5)

@app.get("/")
def home():
    return {"message": "FastAPI Backend Running on Port 9567"}

@app.post("/insert")
def insert(text: str = Form(...)):
    doc_count = es.count(index=INDEX_NAME)["count"]
    doc_id = str(doc_count + 1)
    doc = {"id": doc_id, "text": text}

    res = es.index(index=INDEX_NAME, id=doc_id, document=doc)

    verify_res = es.get(index=INDEX_NAME, id=doc_id, ignore=[404])
    if not verify_res or "_source" not in verify_res:
        return {"message": "Failed to store data"}

    return {"message": "Stored successfully", "id": doc_id, "text": text}

@app.get("/search")
def search(query: str):
    body = {
        "query": {
            "match": {
                "text": {
                    "query": query,
                    "fuzziness": "AUTO"  # Enables typo handling
                }
            }
        },
        "size": 1,
        "sort": ["_score"]
    }
    res = es.search(index=INDEX_NAME, body=body)
    
    if res["hits"]["hits"]:
        best_doc = res["hits"]["hits"][0]
        return {
            "message": "Best document found",
            "id": best_doc["_source"].get("id", "unknown"),
            "text": best_doc["_source"].get("text", "No text available")
        }
    
    return {"message": "No data"}

