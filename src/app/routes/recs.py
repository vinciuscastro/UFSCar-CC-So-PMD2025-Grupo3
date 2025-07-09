"""
Module for the 'recs/' route.
"""
from flask import Blueprint, jsonify, request
from configs import mongodb, neo4j
from configs.errors import Error
from utils import helper

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
