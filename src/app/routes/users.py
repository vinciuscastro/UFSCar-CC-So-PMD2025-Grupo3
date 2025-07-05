"""
Module for the 'users/' route.
"""
import hashlib
from flask import Blueprint, jsonify, request
from connections import mongodb, neo4j

bp = Blueprint("users", __name__)

@bp.route("/", methods=["POST"])
def register_user():
    """
    Endpoint for registering a new user.
    """
    body = request.get_json()

    if not body or 'username' not in body or 'password' not in body:
        return jsonify({"error": "username and password are required"}), 400

    username = body['username']
    password = body['password']
    name = body.get('name')
    bio = body.get('bio')

    existing_user = mongodb.db.users.count_documents({"username": username}, limit=1) > 0
    if existing_user:
        return jsonify({"error": "Username already exists"}), 409

    user = {}
    user["username"] = username
    user["password"] = hashlib.sha256(password.encode('utf-8')).hexdigest()
    if name:
        user["name"] = name
    if bio:
        user["bio"] = bio
    user["friends"] = []
    user["ratings"] = []
    user["follows"] = []

    mongodb.db.users.insert_one(user)

    neo4j.driver.execute_query(
        """
        MERGE (u:User {username: $username})
        """,
        username = username
    )

    return jsonify(), 201

@bp.route("/<username>", methods=["DELETE"])
def delete_user(username):
    """
    Endpoint for deleting a user account.
    """
    user = mongodb.db.users.find_one(
        {
            "username": username,
        },
        {
            "friends": True,
            "ratings": True,
            "follows": True,
        },
    )
    if not user:
        return jsonify({"error": "User not found"}), 404

    for friend in user["friends"]:
        mongodb.db.users.update_one(
            {
                "username": friend,
            },
            {
                "$pull": {
                    "friends": {
                        "username": username,
                    },
                },
            },
        )

    for rating in user["ratings"]:
        mongodb.db.artists.update_one(
            {
                "releases.id": rating["id"],
            },
            {
                "$pull": {
                    "releases.$.ratings": {
                        "username": username,
                    }
                }
            }
        )

    for follow in user["follows"]:
        mongodb.db.artists.update_one(
            {
                "_id": follow["id"],
            },
            {
                "$inc": {
                    "qt_followers": -1,
                },
            },
        )

    mongodb.db.users.delete_one(
        {
            "username": username,
        },
    )

    neo4j.driver.execute_query(
        """
        MATCH (u:User {username: $username})
        DETACH DELETE u
        """,
        username=username,
    )

    return jsonify(), 200

@bp.route("/<username>", methods=["PATCH"])
def update_user(username):
    """
    Endpoint for updating user data (password, name, bio).
    """
    body = request.get_json()
    if not body:
        return jsonify({"error": "Request body is required"}), 400

    user_exists = mongodb.db.users.count_documents({"username": username}, limit=1) > 0
    if not user_exists:
        return jsonify({"error": "User not found"}), 404

    update_ops = {}
    unset_ops = {}

    if 'password' in body:
        password = body['password']
        update_ops["password"] = hashlib.sha256(password.encode('utf-8')).hexdigest()

    if 'name' in body:
        name = body['name']
        if name:
            update_ops["name"] = name
        else:
            unset_ops["name"] = True

    if 'bio' in body:
        bio = body['bio']
        if bio:
            update_ops["bio"] = bio
        else:
            unset_ops["bio"] = True

    if not update_ops and not unset_ops:
        return jsonify({"error": "No valid fields to update"}), 400

    update_doc = {}
    if update_ops:
        update_doc["$set"] = update_ops
    if unset_ops:
        update_doc["$unset"] = unset_ops

    result = mongodb.db.users.update_one(
        {
            "username": username,
        },
        update_doc,
    )

    if result.modified_count == 0:
        return jsonify({"error": "No changes made"}), 400

    return jsonify(), 200

@bp.route("/<username>", methods=["GET"])
def get_user(username):
    """
    Endpoint for getting the user resource by username.
    """
    user_cursor = mongodb.db.users.aggregate([
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

@bp.route("/<username>/friends", methods=["GET"])
def get_user_friends(username):
    """
    Endpoint for getting all friends of a user.
    """
    user_cursor = mongodb.db.users.aggregate([
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

@bp.route("/<username>/ratings", methods=["GET"])
def get_user_ratings(username):
    """
    Endpoint for getting all ratings of a user.
    """
    user_cursor = mongodb.db.users.aggregate([
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

@bp.route("/<username>/follows", methods=["GET"])
def get_user_follows(username):
    """
    Endpoint for getting all artists followed by a user.
    """
    user_cursor = mongodb.db.users.aggregate([
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

@bp.route("/<username>/ratings", methods=["POST"])
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

    user_exists = mongodb.db.users.count_documents({"username": username}, limit=1) > 0
    if not user_exists:
        return jsonify({"error": "User not found"}), 404

    release_cursor = mongodb.db.artists.aggregate([
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

    record, _, _ = neo4j.driver.execute_query(
        """
        MATCH (u:User {username: $username})-[:RATED]->(r:Release {id: $release_id})
        RETURN 1
        """,
        username=username,
        release_id=release["id"],
    )
    if record:
        return jsonify({"error": "Duplicate rating"}), 400

    mongodb.db.users.update_one(
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

    mongodb.db.artists.update_one(
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

    neo4j.driver.execute_query(
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

@bp.route("/<username>/ratings/<release_id>", methods=["DELETE"])
def unrate_release(username, release_id):
    """
    Endpoint for removing a rating from a user and release.
    """
    user_exists = mongodb.db.users.count_documents({"username": username}, limit=1) > 0
    if not user_exists:
        return jsonify({"error": "User not found"}), 404

    release_exists = mongodb.db.artists.count_documents(
        {
            "releases.id": release_id,
        },
        limit=1,
    ) > 0
    if not release_exists:
        return jsonify({"error": "Release not found"}), 404

    record, _, _ = neo4j.driver.execute_query(
        """
        MATCH (u:User {username: $username})-[:RATED]->(r:Release {id: $release_id})
        RETURN 1
        """,
        username=username,
        release_id=release_id,
    )
    if not record:
        return jsonify({"error": "Rating not found"}), 404

    mongodb.db.users.update_one(
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

    mongodb.db.artists.update_one(
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

    neo4j.driver.execute_query(
        """
        MATCH (u:User {username: $username})-[r:RATED]->(rel:Release {id: $release_id})
        DELETE r
        """,
        username=username,
        release_id=release_id,
    )

    return jsonify(), 200

@bp.route("/<username>/follows", methods=["POST"])
def follow_artist(username):
    """
    Endpoint for following an artist.
    """
    body = request.get_json()

    if not body or 'id' not in body:
        return jsonify({"error": "id is required"}), 400

    artist_id = body['id']

    user_exists = mongodb.db.users.count_documents({"username": username}, limit=1) > 0
    if not user_exists:
        return jsonify({"error": "User not found"}), 404

    artist = mongodb.db.artists.find_one(
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

    record, _, _ = neo4j.driver.execute_query(
        """
        MATCH (u:User {username: $username})-[:FOLLOWS]->(a:Artist {id: $artist_id})
        RETURN 1
        """,
        username = username,
        artist_id = artist_id,
    )
    if record:
        return jsonify({"error": "Already following this artist"}), 400

    mongodb.db.users.update_one(
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

    mongodb.db.artists.update_one(
        {
            "_id": artist_id,
        },
        {
            "$inc": {
                "qt_followers": 1,
            },
        },
    )

    neo4j.driver.execute_query(
        """
        MATCH (u:User {username: $username})
        MATCH (a:Artist {id: $artist_id})
        MERGE (u)-[:FOLLOWS]->(a)
        """,
        artist_id = artist_id,
        username = username,
    )

    return jsonify(), 201

@bp.route("/<username>/follows/<artist_id>", methods=["DELETE"])
def unfollow_artist(username, artist_id):
    """
    Endpoint for unfollowing an artist.
    """
    user_exists = mongodb.db.users.count_documents({"username": username}, limit=1) > 0
    if not user_exists:
        return jsonify({"error": "User not found"}), 404

    artist_exists = mongodb.db.artists.count_documents({"_id": artist_id}, limit=1) > 0
    if not artist_exists:
        return jsonify({"error": "Artist not found"}), 404

    record, _, _ = neo4j.driver.execute_query(
        """
        MATCH (u:User {username: $username})-[:FOLLOWS]->(a:Artist {id: $artist_id})
        RETURN 1
        """,
        username = username,
        artist_id = artist_id,
    )
    if not record:
        return jsonify({"error": "Not following this artist"}), 404

    mongodb.db.users.update_one(
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

    mongodb.db.artists.update_one(
        {
            "_id": artist_id,
        },
        {
            "$inc": {
                "qt_followers": -1,
            },
        },
    )

    neo4j.driver.execute_query(
        """
        MATCH (u:User {username: $username})-[f:FOLLOWS]->(a:Artist {id: $artist_id})
        DELETE f
        """,
        username = username,
        artist_id = artist_id   ,
    )

    return jsonify(), 200

@bp.route("/<username>/friends", methods=["POST"])
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

    user_exists = mongodb.db.users.count_documents({"username": username}, limit=1) > 0
    if not user_exists:
        return jsonify({"error": "User not found"}), 404

    friend_exists = mongodb.db.users.count_documents({"username": friend_username}, limit=1) > 0
    if not friend_exists:
        return jsonify({"error": "Friend not found"}), 404

    record, _, _ = neo4j.driver.execute_query(
        """
        MATCH (u1:User {username: $username})-[:FRIENDS_WITH]-(u2:User {username: $friend_username})
        RETURN 1
        """,
        username=username,
        friend_username=friend_username,
    )
    if record:
        return jsonify({"error": "Already friends with this user"}), 400

    mongodb.db.users.update_one(
        {
            "username": username,
        },
        {
            "$push": {
                "friends": friend_username,
            },
        },
    )

    mongodb.db.users.update_one(
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

    neo4j.driver.execute_query(
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

@bp.route("/<username>/friends/<friend_username>", methods=["DELETE"])
def unfriend_user(username, friend_username):
    """
    Endpoint for removing a friend.
    """
    user_exists = mongodb.db.users.count_documents({"username": username}, limit=1) > 0
    if not user_exists:
        return jsonify({"error": "User not found"}), 404

    friend_exists = mongodb.db.users.count_documents({"username": friend_username}, limit=1) > 0
    if not friend_exists:
        return jsonify({"error": "Friend not found"}), 404

    record, _, _ = neo4j.driver.execute_query(
        """
        MATCH (u1:User {username: $username})-[:FRIENDS_WITH]-(u2:User {username: $friend_username})
        RETURN 1
        """,
        username=username,
        friend_username=friend_username,
    )
    if not record:
        return jsonify({"error": "Not friends with this user"}), 404

    mongodb.db.users.update_one(
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

    mongodb.db.users.update_one(
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

    neo4j.driver.execute_query(
        """
        MATCH (u1:User {username: $username})-[f1:FRIENDS_WITH]->(u2:User {username: $friend_username})
        MATCH (u1)<-[f2:FRIENDS_WITH]-(u2)
        DELETE f1, f2
        """,
        username=username,
        friend_username=friend_username,
    )

    return jsonify(), 200
