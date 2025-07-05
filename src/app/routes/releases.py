"""
Module for the 'releases/' route.
"""
from flask import Blueprint, jsonify
from connections import mongodb

bp = Blueprint("releases", __name__)

@bp.route("/<release_id>", methods = ["GET"])
def get_release(release_id):
    """
    Endpoint for getting the release resource by release ID.
    """
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

@bp.route("/<release_id>/ratings", methods = ["GET"])
def get_release_ratings(release_id):
    """
    Endpoint for getting all ratings for a specific release.
    """
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
                "release": {
                    "id": "$releases.id",
                    "name": "$releases.name",
                    "artist": {
                        "id": "$_id",
                        "name": "$name"
                    }
                },
                "items": "$releases.ratings"
            }
        }
    ])

    release_results = tuple(release_cursor)
    if not release_results:
        return jsonify({"error": "Release not found"}), 404

    return jsonify(release_results[0])
