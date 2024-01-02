from flask import Blueprint, request, jsonify

from database import db_update_link_record, db_get_sent

routes_blueprint = Blueprint("routes_blueprint", __name__)


@routes_blueprint.route("/update_link/<int:link_id>", methods=["POST"])
def update_link(link_id):
    try:
        data = request.json

        db_update_link_record(
            link_id=link_id,
            new_link=data.get("link"),
            new_content_file=data.get("content_file"),
            new_email=data.get("email", "").lower(),
            new_contact_name=data.get("contact_name", "").upper(),
            new_pronoun=data.get("pronoun"),
            new_industry=data.get("industry", "").upper(),
            new_city=data.get("city", "").upper(),
            new_area=data.get("area", "").upper(),
            new_parsed=data.get("parsed"),
            new_contacted_at=data.get("contacted_at"),
        )

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
