import os
import json
import dotenv
from flask import Flask
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from neo4j import GraphDatabase

dotenv.load_dotenv()

app = Flask(__name__)

mongo_client = MongoClient(
    (f"mongodb+srv://{os.getenv("MONGODB_USERNAME")}:{os.getenv("MONGODB_PASSWORD")}"
    "@projeto-bd.9scqvyv.mongodb.net/"
    "?retryWrites=true&w=majority&appName=projeto-bd"),
    server_api = ServerApi(
        version = "1",
        strict = True,
        deprecation_errors = True
    )
)
mongo_db = mongo_client["music_catalog"]

neo4j = GraphDatabase.driver(
    "neo4j+s://10ab7e50.databases.neo4j.io",
    auth=(
        os.getenv("NEO4J_USERNAME"),
        os.getenv("NEO4J_PASSWORD"),
    ),
)
neo4j.verify_connectivity()

@app.route("/v1/artists/<artist_id>", methods=["GET"])
def hello_api(artist_id):
    artist = mongo_db.artists.find_one(
        {
            "_id": artist_id
        }
    )

    return json.dumps(artist)

if __name__=="__main__":
    app.run(debug=True)

    mongo_client.close()
    neo4j.close()
