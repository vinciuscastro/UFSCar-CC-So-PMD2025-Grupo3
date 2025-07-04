"""
Server for the music catalog API
"""

import os
import dotenv
from flask import Flask, jsonify, request
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from neo4j import GraphDatabase

dotenv.load_dotenv()

app = Flask(__name__)
app.json.sort_keys = False

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
def get_artist(artist_id):
    """
    Endpoint for getting the artist resource by artist ID.
    """
    artist = mongo_db.artists.find_one(
        {
            "_id": artist_id
        }
    )

    if not artist:
        return jsonify(), 404

    artist = {"id" if k == "_id" else k: v for k, v in artist.items()}
    return jsonify(artist)

@app.route("/v1/users/<username>", methods=["GET"])
def get_user(username):
    """
    Endpoint for getting the user resource by username.
    """
    user = mongo_db.users.find_one(
        {
            "username": username,
        },
        {
            "_id": False,
        },
    )

    if not user:
        return jsonify(), 404

    return jsonify(user)

@app.route("/v1/recommendations/artists/<genre>", methods=["GET"])
def get_artist_recs_by_genre(genre):
    """
    Endpoint for getting artist recommendations by genre.
    """
    limit = request.args.get("limit", default=10, type=int)
    if limit <= 0:
        return jsonify({"error": "Limit must be a positive integer"}), 400

    limit = min(limit, 100)

    records, _, _ = neo4j.execute_query(
        """
        MATCH (a:Artist)-[:BELONGS_TO]->(g:Genre {name: $genre})
        RETURN a.id AS artist_id
        ORDER BY a.popularity DESC
        LIMIT $limit
        """,
        genre=genre,
        limit=limit
    )

    artists = []

    for record in records:
        artist = mongo_db.artists.find_one(
            {
                "_id": record["artist_id"],
            },
            {
                "_id": False,
                "id": "$_id",
                "name": True,
                "genres": True,
                "bio": True,
            },
        )

        artists.append(artist)

    if not artists:
        return jsonify(), 404

    return jsonify(artists)


if __name__=="__main__":
    app.run(debug=True)

    mongo_client.close()
    neo4j.close()
