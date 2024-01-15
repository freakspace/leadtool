from flask import Blueprint, request, jsonify

from database import (
    db_update_link_record,
    db_get_sent,
    db_create_link,
    db_get_links,
    db_get_unparsed_links,
    db_create_user,
    db_get_campaigns,
)

routes_blueprint = Blueprint("routes_blueprint", __name__)


@routes_blueprint.route("/update_link/<int:link_id>", methods=["POST"])
def update_link(link_id):
    try:
        data = request.json

        # Prepare a dictionary of arguments
        args = {
            "link_id": link_id,
            "link": data.get("link"),
            "content_file": data.get("content_file"),
            "email": data.get("email", "").lower()
            if data.get("email") is not None
            else None,
            "contact_name": data.get("contact_name", "").title()
            if data.get("contact_name") is not None
            else None,
            "pronoun": data.get("pronoun"),
            "industry": data.get("industry", "").title()
            if data.get("industry") is not None
            else None,
            "city": data.get("city", "").title()
            if data.get("city") is not None
            else None,
            "area": data.get("area", "").title()
            if data.get("area") is not None
            else None,
            "parsed": data.get("parsed"),
            "invalid": data.get("invalid"),
            "contacted_at": data.get("contacted_at"),
            "classification": data.get("classification")
            if data.get("classification") is not None
            else None,
        }

        # Remove None values
        args = {k: v for k, v in args.items() if v is not None}

        # Call the function with unpacked arguments
        db_update_link_record(**args)

        return jsonify({"message": "Link updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@routes_blueprint.route("/check_sent", methods=["POST"])
def check_sent():
    data = request.json
    domain = data.get("domain")
    email = data.get("email")
    result = db_get_sent(domain=domain, email=email)
    return jsonify({"sent": result})


@routes_blueprint.route("/create_link", methods=["POST"])
def create_link():
    data = request.json
    link = data.get("link")
    db_create_link(link=link)
    return jsonify({"message": "Link created successfully"}), 200


@routes_blueprint.route("/links", methods=["GET"])
def get_links():
    links = db_get_links()
    return jsonify({"links": links}), 200


@routes_blueprint.route("/campaigns", methods=["GET"])
def get_campaigns():
    campaigns = db_get_campaigns()
    return jsonify({"campaigns": campaigns}), 200


@routes_blueprint.route("/links_for_parsing", methods=["GET"])
def get_links_for_pasing():
    links = db_get_unparsed_links()
    return jsonify({"links": links}), 200


@routes_blueprint.route("/create_user", methods=["POST"])
def create_user():
    data = request.json

    username = data.get("username")
    password = data.get("password")
    superuser = data.get("superuser", 0)

    db_create_user(username=username, password=password, superuser=superuser)

    return jsonify({"message": "User created successfully"}), 200
