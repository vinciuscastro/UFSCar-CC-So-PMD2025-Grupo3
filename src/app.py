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
    artist_cursor = mongo_db.artists.aggregate([
        {
            "$match": {
                "_id": artist_id
            }
        },
        {
            "$addFields": {
                "allRatings": {
                    "$reduce": {
                        "input": "$releases",
                        "initialValue": [],
                        "in": {
                            "$concatArrays": [
                                "$$value",
                                "$$this.ratings"
                            ]
                        }
                    }
                },
                "mappedReleases": {
                    "$map": {
                        "input": "$releases",
                        "as": "release",
                        "in": {
                            "id": "$$release.id",
                            "name": "$$release.name",
                            "release_year": {
                                "$year": {
                                    "$dateFromString": {
                                        "dateString": "$$release.release_date"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        {
            "$project": {
                "_id": False,
                "id": "$_id",
                "name": True,
                "genres": True,
                "bio": True,
                "qt_followers": True,
                "average_rating": {
                    "$cond": {
                        "if": {
                            "$gt": [{"$size": "$allRatings"}, 0],
                        },
                        "then": {
                            "$avg": "$allRatings.rating"
                        },
                        "else": None
                    }
                },
                "releases": "$mappedReleases"
            }
        }
    ])

    artists_retrieved = tuple(artist_cursor)

    if not artists_retrieved:
        return jsonify(), 404

    return jsonify(artists_retrieved[0])


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

@app.route("/v1/users/<username>/ratings", methods=["POST"])
def rate_release(username):
    """
    Endpoint for adding a rating to a user and release.
    """
    body = request.get_json()

    if not body or 'release_id' not in body or 'rating' not in body:
        return jsonify({"error": "release_id and rating are required"}), 400

    release_id = body['release_id']
    rating = body['rating']

    if not isinstance(rating, int) or rating < 0 or rating > 10:
        return jsonify({"error": "Rating must be a number between 0 and 10"}), 400

    user_exists = mongo_db.users.count_documents({"username": username}, limit=1) > 0
    if not user_exists:
        return jsonify({"error": "User not found"}), 404

    release_cursor = mongo_db.artists.aggregate([
        {
            "$match": {
                "releases.id": release_id
            }
        },
        {
            "$unwind": "$releases"
        },
        {
            "$match": {
                "releases.id": release_id
            }
        },
        {
            "$project": {
                "_id": False,
                "id": "$releases.id",
                "artist_name": "$name",
                "name": "$releases.name",
            }
        }
    ])

    release_results = tuple(release_cursor)
    release = release_results[0] if release_results else None
    if not release:
        return jsonify({"error": "Release not found"}), 404

    record, _, _ = neo4j.execute_query(
        """
        MATCH (u:User {username: $username})-[:RATED]->(r:Release {id: $release_id})
        RETURN 1
        """,
        username=username,
        release_id=release["id"],
    )
    if record:
        return jsonify({"error": "Duplicate rating"}), 400

    mongo_db.users.update_one(
        {
            "username": username,
        },
        {
            "$push": {
                "ratings": {
                    "release_id": release["id"],
                    "artist_name": release["artist_name"],
                    "release_name": release["name"],
                    "rating": rating,
                },
            },
        },
    )

    mongo_db.artists.update_one(
        {
            "releases.id": release_id,
        },
        {
            "$push": {
                "releases.$.ratings": {
                    "username": username,
                    "rating": rating
                }
            }
        }
    )

    neo4j.execute_query(
        """
        MATCH (r:Release {id: $release_id})
        MATCH (u:User {username: $username})
        MERGE (u)-[rel:RATED]->(r)
        ON CREATE SET rel.rating = $rating
        """,
        release_id=release["id"],
        username=username,
        rating=rating,
    )

    return jsonify(), 201

@app.route("/v1/users/<username>/follows", methods=["POST"])
def follow_artist(username):
    """
    Endpoint for following an artist.
    """
    body = request.get_json()

    if not body or 'artist_id' not in body:
        return jsonify({"error": "artist_id is required"}), 400

    artist_id = body['artist_id']

    user_exists = mongo_db.users.count_documents({"username": username}, limit=1) > 0
    if not user_exists:
        return jsonify({"error": "User not found"}), 404

    artist = mongo_db.artists.find_one(
        {
            "_id": artist_id,
        },
        {
            "_id": True,
            "name": True,
        },
    )
    if not artist:
        return jsonify({"error": "Artist not found"}), 404

    record, _, _ = neo4j.execute_query(
        """
        MATCH (u:User {username: $username})-[:FOLLOWS]->(a:Artist {id: $artist_id})
        RETURN 1
        """,
        username=username,
        artist_id=artist_id,
    )
    if record:
        return jsonify({"error": "Already following this artist"}), 400

    mongo_db.users.update_one(
        {
            "username": username,
        },
        {
            "$push": {
                "follows": {
                    "artist_id": artist_id,
                    "artist_name": artist["name"]
                },
            },
        },
    )

    mongo_db.artists.update_one(
        {
            "_id": artist_id,
        },
        {
            "$inc": {
                "qt_followers": 1,
            },
        },
    )

    neo4j.execute_query(
        """
        MATCH (u:User {username: $username})
        MATCH (a:Artist {id: $artist_id})
        MERGE (u)-[:FOLLOWS]->(a)
        """,
        artist_id=artist_id,
        username=username,
    )

    return jsonify({"message": "Successfully followed artist"}), 201

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
