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

@app.route("/v1/artists/<artist_id>/tracks", methods=["GET"])
def get_artist_tracks(artist_id):
    """
    Endpoint for getting all tracks from an artist in alphabetical order.
    """
    tracks_cursor = mongo_db.artists.aggregate([
        {
            "$match": {
                "_id": artist_id,
            },
        },
        {
            "$unwind": "$releases",
        },
        {
            "$unwind": "$releases.tracks",
        },
        {
            "$group": {
                "_id": {
                    "artist_id": "$_id",
                    "artist_name": "$name",
                    "track_name": "$releases.tracks.name"
                },
                "releases": {
                    "$push": {
                        "id": "$releases.id",
                        "name": "$releases.name",
                    },
                },
            },
        },
        {
            "$group": {
                "_id": {
                    "artist_id": "$_id.artist_id",
                    "artist_name": "$_id.artist_name"
                },
                "items": {
                    "$push": {
                        "name": "$_id.track_name",
                        "releases": "$releases",
                    },
                },
            },
        },
        {
            "$project": {
                "_id": False,
                "artist_id": "$_id.artist_id",
                "artist_name": "$_id.artist_name",
                "items": {
                    "$sortArray": {
                        "input": "$items",
                        "sortBy": {
                            "name": 1,
                        },
                    },
                },
            },
        },
    ])

    tracks_results = list(tracks_cursor)

    if not tracks_results:
        return jsonify({"error": "Artist not found"}), 404

    return jsonify(tracks_results[0])


@app.route("/v1/releases/<release_id>", methods=["GET"])
def get_release(release_id):
    """
    Endpoint for getting the release resource by release ID.
    """
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
                "name": "$releases.name",
                "artist": {
                    "id": "$_id",
                    "name": "$name"
                },
                "release_date": "$releases.release_date",
                "rating_average": {
                    "$cond": {
                        "if": {
                            "$gt": [{"$size": "$releases.ratings"}, 0],
                        },
                        "then": {
                            "$avg": "$releases.ratings.rating",
                        },
                        "else": None
                    }
                },
                "tracks": "$releases.tracks"
            }
        }
    ])

    release_results = tuple(release_cursor)
    if not release_results:
        return jsonify(), 404

    return jsonify(release_results[0])

@app.route("/v1/releases/<release_id>/ratings", methods=["GET"])
def get_release_ratings(release_id):
    """
    Endpoint for getting all ratings for a specific release.
    """
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
                "release_id": "$releases.id",
                "release_name": "$releases.name",
                "release_artist": "$name",
                "items": "$releases.ratings"
            }
        }
    ])

    release_results = tuple(release_cursor)
    if not release_results:
        return jsonify({"error": "Release not found"}), 404

    return jsonify(release_results[0])


@app.route("/v1/users/<username>", methods=["GET"])
def get_user(username):
    """
    Endpoint for getting the user resource by username.
    """
    user_cursor = mongo_db.users.aggregate([
        {
            "$match": {
                "username": username,
            },
        },
        {
            "$project": {
                "_id": False,
                "username": True,
                "name": {
                    "$ifNull": ["$name", None]
                },
                "bio": {
                    "$ifNull": ["$bio", None]
                },
                "friend_count": {
                    "$size": "$friends",
                },
                "rating_count": {
                    "$size": "$ratings",
                },
                "follow_count": {
                    "$size": "$follows",
                },
            },
        },
    ])

    user_results = tuple(user_cursor)
    if not user_results:
        return jsonify(), 404

    return jsonify(user_results[0])

@app.route("/v1/users/<username>/friends", methods=["GET"])
def get_user_friends(username):
    """
    Endpoint for getting all friends of a user.
    """
    user_cursor = mongo_db.users.aggregate([
        {
            "$match": {
                "username": username,
            }
        },
        {
            "$project": {
                "_id": False,
                "username": True,
                "items": "$friends",
            },
        },
    ])

    user_results = tuple(user_cursor)
    if not user_results:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user_results[0])

@app.route("/v1/users/<username>/ratings", methods=["GET"])
def get_user_ratings(username):
    """
    Endpoint for getting all ratings of a user.
    """
    user_cursor = mongo_db.users.aggregate([
        {
            "$match": {
                "username": username,
            }
        },
        {
            "$project": {
                "_id": False,
                "username": True,
                "items": "$ratings",
            },
        },
    ])

    user_results = tuple(user_cursor)
    if not user_results:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user_results[0])

@app.route("/v1/users/<username>/follows", methods=["GET"])
def get_user_follows(username):
    """
    Endpoint for getting all artists followed by a user.
    """
    user_cursor = mongo_db.users.aggregate([
        {
            "$match": {
                "username": username,
            }
        },
        {
            "$project": {
                "_id": False,
                "username": True,
                "items": "$follows",
            },
        },
    ])

    user_results = tuple(user_cursor)
    if not user_results:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user_results[0])


@app.route("/v1/users/<username>/ratings", methods=["POST"])
def rate_release(username):
    """
    Endpoint for adding a rating to a user and release.
    """
    body = request.get_json()

    if not body or 'id' not in body or 'rating' not in body:
        return jsonify({"error": "id and rating are required"}), 400

    release_id = body['id']
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
                "artist": "$name",
                "name": "$releases.name",
            }
        }
    ])

    release_results = tuple(release_cursor)
    if not release_results:
        return jsonify({"error": "Release not found"}), 404

    release: dict = release_results[0]

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
                    "id": release["id"],
                    "artist": release["artist"],
                    "name": release["name"],
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

@app.route("/v1/users/<username>/ratings/<release_id>", methods=["DELETE"])
def unrate_release(username, release_id):
    """
    Endpoint for removing a rating from a user and release.
    """
    user_exists = mongo_db.users.count_documents({"username": username}, limit=1) > 0
    if not user_exists:
        return jsonify({"error": "User not found"}), 404

    release_exists = mongo_db.artists.count_documents(
        {
            "releases.id": release_id,
        },
        limit=1,
    ) > 0
    if not release_exists:
        return jsonify({"error": "Release not found"}), 404

    record, _, _ = neo4j.execute_query(
        """
        MATCH (u:User {username: $username})-[:RATED]->(r:Release {id: $release_id})
        RETURN 1
        """,
        username=username,
        release_id=release_id,
    )
    if not record:
        return jsonify({"error": "Rating not found"}), 404

    mongo_db.users.update_one(
        {
            "username": username,
        },
        {
            "$pull": {
                "ratings": {
                    "id": release_id,
                },
            },
        },
    )

    mongo_db.artists.update_one(
        {
            "releases.id": release_id,
        },
        {
            "$pull": {
                "releases.$.ratings": {
                    "username": username,
                },
            },
        },
    )

    neo4j.execute_query(
        """
        MATCH (u:User {username: $username})-[r:RATED]->(rel:Release {id: $release_id})
        DELETE r
        """,
        username=username,
        release_id=release_id,
    )

    return jsonify(), 200

@app.route("/v1/users/<username>/follows", methods=["POST"])
def follow_artist(username):
    """
    Endpoint for following an artist.
    """
    body = request.get_json()

    if not body or 'id' not in body:
        return jsonify({"error": "id is required"}), 400

    artist_id = body['id']

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
        username = username,
        artist_id = artist_id,
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
                    "id": artist_id,
                    "name": artist["name"]
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
        artist_id = artist_id,
        username = username,
    )

    return jsonify(), 201

@app.route("/v1/users/<username>/follows/<artist_id>", methods=["DELETE"])
def unfollow_artist(username, artist_id):
    """
    Endpoint for unfollowing an artist.
    """
    user_exists = mongo_db.users.count_documents({"username": username}, limit=1) > 0
    if not user_exists:
        return jsonify({"error": "User not found"}), 404

    artist_exists = mongo_db.artists.count_documents({"_id": artist_id}, limit=1) > 0
    if not artist_exists:
        return jsonify({"error": "Artist not found"}), 404

    record, _, _ = neo4j.execute_query(
        """
        MATCH (u:User {username: $username})-[:FOLLOWS]->(a:Artist {id: $artist_id})
        RETURN 1
        """,
        username = username,
        artist_id = artist_id,
    )
    if not record:
        return jsonify({"error": "Not following this artist"}), 404

    mongo_db.users.update_one(
        {
            "username": username,
        },
        {
            "$pull": {
                "follows": {
                    "id": artist_id,
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
                "qt_followers": -1,
            },
        },
    )

    neo4j.execute_query(
        """
        MATCH (u:User {username: $username})-[f:FOLLOWS]->(a:Artist {id: $artist_id})
        DELETE f
        """,
        username = username,
        artist_id = artist_id   ,
    )

    return jsonify(), 200

@app.route("/v1/users/<username>/friends", methods=["POST"])
def befriend_user(username):
    """
    Endpoint for adding a friend.
    """
    body = request.get_json()
    if not body or 'username' not in body:
        return jsonify({"error": "username is required"}), 400

    friend_username = body['username']
    if username == friend_username:
        return jsonify({"error": "Cannot befriend yourself"}), 400

    user_exists = mongo_db.users.count_documents({"username": username}, limit=1) > 0
    if not user_exists:
        return jsonify({"error": "User not found"}), 404

    friend_exists = mongo_db.users.count_documents({"username": friend_username}, limit=1) > 0
    if not friend_exists:
        return jsonify({"error": "Friend not found"}), 404

    record, _, _ = neo4j.execute_query(
        """
        MATCH (u1:User {username: $username})-[:FRIENDS_WITH]-(u2:User {username: $friend_username})
        RETURN 1
        """,
        username=username,
        friend_username=friend_username,
    )
    if record:
        return jsonify({"error": "Already friends with this user"}), 400

    mongo_db.users.update_one(
        {
            "username": username,
        },
        {
            "$push": {
                "friends": {
                    "username": friend_username,
                },
            },
        },
    )

    mongo_db.users.update_one(
        {
            "username": friend_username,
        },
        {
            "$push": {
                "friends": {
                    "username": username,
                },
            },
        },
    )

    neo4j.execute_query(
        """
        MATCH (u1:User {username: $username})
        MATCH (u2:User {username: $friend_username})
        MERGE (u1)-[:FRIENDS_WITH]->(u2)
        MERGE (u1)<-[:FRIENDS_WITH]-(u2)
        """,
        username=username,
        friend_username=friend_username,
    )

    return jsonify(), 201

@app.route("/v1/users/<username>/friends/<friend_username>", methods=["DELETE"])
def unfriend_user(username, friend_username):
    """
    Endpoint for removing a friend.
    """
    user_exists = mongo_db.users.count_documents({"username": username}, limit=1) > 0
    if not user_exists:
        return jsonify({"error": "User not found"}), 404

    friend_exists = mongo_db.users.count_documents({"username": friend_username}, limit=1) > 0
    if not friend_exists:
        return jsonify({"error": "Friend not found"}), 404

    record, _, _ = neo4j.execute_query(
        """
        MATCH (u1:User {username: $username})-[:FRIENDS_WITH]-(u2:User {username: $friend_username})
        RETURN 1
        """,
        username=username,
        friend_username=friend_username,
    )
    if not record:
        return jsonify({"error": "Not friends with this user"}), 404

    mongo_db.users.update_one(
        {
            "username": username,
        },
        {
            "$pull": {
                "friends": {
                    "username": friend_username,
                },
            },
        },
    )

    mongo_db.users.update_one(
        {
            "username": friend_username,
        },
        {
            "$pull": {
                "friends": {
                    "username": username,
                },
            },
        },
    )

    neo4j.execute_query(
        """
        MATCH (u1:User {username: $username})-[f1:FRIENDS_WITH]->(u2:User {username: $friend_username})
        MATCH (u1)<-[f2:FRIENDS_WITH]-(u2)
        DELETE f1, f2
        """,
        username=username,
        friend_username=friend_username,
    )

    return jsonify(), 200


@app.route("/v1/users/<username>/recs/artists/<genre>", methods=["GET"])
def get_artist_recs_by_genre(username, genre):
    """
    Endpoint for getting artist recommendations by genre.
    """
    limit = request.args.get("limit", default=5, type=int)
    limit = min(limit, 50)
    if limit <= 0:
        return jsonify({"error": "Limit must be a positive integer"}), 400

    records, _, _ = neo4j.execute_query(
        """
        MATCH (a:Artist)-[:BELONGS_TO]->(g:Genre {name: $genre})
        WHERE NOT EXISTS {
            MATCH (u:User {username: $username})-[:FOLLOWS]->(a)
        }
        RETURN a.id AS id
        ORDER BY a.popularity DESC
        LIMIT $limit
        """,
        genre=genre,
        username=username,
        limit=limit
    )
    if not records:
        return jsonify({"error": "No artists found for this genre"}), 404

    artists = []
    for record in records:
        artist = mongo_db.artists.find_one(
            {
                "_id": record["id"],
            },
            {
                "_id": False,
                "id": "$_id",
                "name": True,
                "genres": True,
                "bio": True,
            }
        )
        artists.append(artist)

    return jsonify(artists), 200


if __name__=="__main__":
    app.run(debug=True)

    mongo_client.close()
    neo4j.close()
