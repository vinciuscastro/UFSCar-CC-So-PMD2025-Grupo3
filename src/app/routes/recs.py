"""
Module for the 'recs/' route.
"""
from flask import Blueprint, jsonify, request
from connections import mongodb, neo4j

bp = Blueprint("recs", __name__)

@bp.route("/<username>/artists/<genre>", methods = ["GET"])
def get_artist_recs_by_genre(username, genre):
    """
    Endpoint for getting artist recommendations by genre.
    """
    limit = request.args.get("limit", default = 5, type = int)
    limit = min(limit, 50)
    if limit <= 0:
        return jsonify({"error": "Limit must be a positive integer"}), 400

    user_exists = mongodb.db.users.count_documents({"username": username}, limit = 1) > 0
    if not user_exists:
        return jsonify({"error": "User not found"}), 404

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
        return jsonify({"error": "No artists found for this genre"}), 404

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
