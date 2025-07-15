"""
Module for the 'recs/' route.
"""
from flask import Blueprint, jsonify, request
from configs import mongodb, neo4j
from configs.errors import Error
from utils import helper
import random

bp = Blueprint("recs", __name__)

@bp.route("/<username>/artists/<genre>", methods = ["GET"])
def get_artist_recs_by_genre(username, genre):
    """
    Endpoint for getting artist recommendations by genre.
    """
    limit = request.args.get("limit", default = 5, type = int)
    limit = min(limit, 50)
    limit = max(1, limit)

    if not helper.exists("user", username):
        return Error.USER_NOT_FOUND.get_response(username = username)
    if not helper.exists("genre", genre):
        return Error.GENRE_NOT_FOUND.get_response(genre = genre)

    records, _, _ = neo4j.driver.execute_query(
        """
        MATCH (a:Artist)-[:BELONGS_TO]->(g:Genre {name: $genre})
        WHERE NOT EXISTS {
            MATCH (u:User {username: $username})-[:FOLLOWS]->(a)
        }
        RETURN a.id AS id
        ORDER BY a.popularity DESC
        LIMIT $limit
        """,
        genre = genre,
        username = username,
        limit = limit
    )
    if not records:
        return Error.ARTIST_RECS_BY_GENRE_NOT_FOUND.get_response(
            username = username,
            genre = genre,
        )

    artists = []
    for record in records:
        artist = mongodb.db.artists.find_one(
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

@bp.route("/<username>/releases/friends", methods = ["GET"])
def get_release_recs_by_friends(username):
    """
    Endpoint for getting release recommendations by friends' positive reviews.
    """
    user = mongodb.db.users.find_one({"username": username})
    if not user:
        return Error.USER_NOT_FOUND.get_response(username=username)

    friends = set(user.get("friends", []))
    friends_rating = neo4j.driver.execute_query(
        """
        MATCH (friend:User)-[r:RATED]->(rel:Release)
        WHERE friend.username IN $friends
        AND r.rating > 6
        RETURN friend.username AS username, rel.id AS release_id, r.rating AS rating
        ORDER BY r.rating DESC
        LIMIT 10
        """,
        friends=list(friends)
    )

    results = []
    for record in friends_rating.records:
        results.append({
            "friend": record["username"],
            "release_id": record["release_id"],
            "rating": record["rating"]
        })

    if not results:
        return Error.NO_FRIENDS_RATINGS_FOUND.get_response(username=username)
    
    first_result = random.choice(results)

    release_cursor = mongodb.db.artists.aggregate([
        {
            "$match": {
                "releases.id": first_result["release_id"],
            },
        },
        {
            "$unwind": "$releases",
        },
        {
            "$match": {
                "releases.id": first_result["release_id"],
            },
        },
        {
            "$project": {
                "_id": False,
                "id": "$releases.id",
                "name": "$releases.name",
                "artist": {
                    "id": "$_id",
                    "name": "$name",
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
                        "else": None,
                    },
                },
                "tracks": "$releases.tracks",
            },
        },
    ])

    release_results = tuple(release_cursor)
    if not release_results:
        return Error.RELEASE_NOT_FOUND.get_response(id = release_results["release_id"])
    
    response = {
        "user": username,
        "friend": first_result["friend"],
        "release": release_results[0]["release"]["name"],
        "rating": first_result["rating"]
    }

    return jsonify(response), 200

@bp.route("/<username>/friends", methods = ["GET"])
def get_friend_recs(username):
    """
    Endpoint for getting friend recommendations.
    """
    user = mongodb.db.users.find_one({"username": username})
    if not user:
        return Error.USER_NOT_FOUND.get_response(username=username)

    friends = set(user.get("friends", []))

    neo4j_result = neo4j.driver.execute_query(
        """
        MATCH (u:User)
        WHERE NOT u.username IN $friends
          AND u.username <> $username
        RETURN u.username AS recommended_user
        ORDER BY rand()
        LIMIT 10
        """,
        friends=list(friends),
        username=username
    )

    recommended_users = []
    for record in neo4j_result.records:
        recommended_users.append(record["recommended_user"])

    response = {
        "user": username,
        "recommended_users": recommended_users
    }

    return jsonify(response), 200

@bp.route("/<username>/friends/genre", methods = ["GET"])
def get_friend_recs_by_genres(username):
    """
    Endpoint for getting friend recommendations by genre affinity.
    """
    user = mongodb.db.users.find_one({"username": username})
    if not user:
        return Error.USER_NOT_FOUND.get_response(username=username)

    friends = set(user.get("friends", []))

    genre_user = neo4j.driver.execute_query(
        """
        MATCH (:User {username: $username})-[:FOLLOWS]->(a:Artist)-[:BELONGS_TO]->(g:Genre)
        RETURN g.name AS genre, count(a) AS count
        ORDER BY count DESC
        LIMIT 1
        """,
        username=username
    )

    if not genre_user.records:
        return Error.NO_GENRE_DATA_FOUND.get_response(username=username)

    most_common_genre = genre_user.records[0]["genre"]

    recs_result = neo4j.driver.execute_query(
        """
        MATCH (u:User)-[:FOLLOWS]->(a:Artist)-[:BELONGS_TO]->(g:Genre)
        WHERE g.name = $genre_name
          AND NOT u.username IN $friends
          AND u.username <> $username
        WITH u, count(a) AS follows_count
        ORDER BY follows_count DESC
        LIMIT 10
        RETURN u.username AS recommended_user
        """,
        genre_name=most_common_genre,
        friends=list(friends),
        username=username
    )

    recommended_users = []
    for record in recs_result.records:
        recommended_users.append({"recommended_users": record["recommended_user"]})

    response = {
        "user": username,
        "genre": most_common_genre,
        "recommended_users": recommended_users
    }

    return jsonify(response), 200

@bp.route("/<username>/friends/review", methods = ["GET"])
def get_friend_recs_by_reviews(username):
    """
    Endpoint for getting friend recommendations by review similarity.
    """

    user = mongodb.db.users.find_one({"username": username})
    if not user:
        return Error.USER_NOT_FOUND.get_response(username=username)

    friends = set(user.get("friends", []))

    reviews = neo4j.driver.execute_query(
        """
        MATCH (u:User)-[r:RATED]->(rel:Release)
        WHERE u.username = $username AND r.rating > 6
        RETURN rel.id AS release_id
        ORDER BY r.rating DESC
        """,
        username=username
    )

    rated_releases = []
    for record in reviews.records:
        rated_releases.append({"release_id": record["release_id"]})

    if not rated_releases:
        return Error.NO_RATINGS_FOUND.get_response(username=username)

    releases_choosed = random.choice(rated_releases)

    rated_reviews = neo4j.driver.execute_query(
        """
        MATCH (u:User)-[r:RATED]->(rel:Release)
        WHERE rel.id = $release_id
        AND r.rating > 6
        AND NOT u.username IN $friends
        AND u.username <> $username
        RETURN u.username AS username
        ORDER BY r.rating DESC
        LIMIT 10
        """,
        release_id=releases_choosed["release_id"],
        friends=list(friends),
        username=username
    )

    recommended_users = []
    for record in rated_reviews.records:
        recommended_users.append({"username": record["username"]})

    release_cursor = mongodb.db.artists.aggregate([
        {
            "$match": {
                "releases.id": releases_choosed["release_id"],
            },
        },
        {
            "$unwind": "$releases",
        },
        {
            "$match": {
                "releases.id": releases_choosed["release_id"],
            },
        },
        {
            "$project": {
                "_id": False,
                "release": {
                    "id": "$releases.id",
                    "name": "$releases.name",
                    "artist": "$name",
                },
                "items": "$releases.ratings",
            },
        },
    ])

    release_results = tuple(release_cursor)
    if not release_results:
        return Error.RELEASE_NOT_FOUND.get_response(id = releases_choosed["release_id"])

    response = {
        "user": username,
        "release": release_results[0]["release"]["name"],
        "recommended_users": recommended_users
    }

    return jsonify(response), 200