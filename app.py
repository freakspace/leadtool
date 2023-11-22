from flask import Flask, render_template, request, redirect, url_for, abort, Response

from database import (
    db_get_lead,
    db_get_leads,
    db_create_lead,
    db_delete_link,
    db_create_campaign,
    db_get_campaign,
    db_get_campaigns,
)

from schema import Link

from utils import generate_csv

app = Flask(__name__, static_folder="content")


def get_lead():
    lead: Link = db_get_lead()

    if not lead:
        return None

    context = {
        "id": lead.id,
        "link": lead.link,
        "email": lead.email,
        "name": lead.contact_name,
        "industry": lead.industry,
        "city": lead.city,
        "area": lead.area,
        "screenshot": f"content/{lead.link}.png",
    }

    return context


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        campaign_name = request.form.get("campaign_name")
        db_create_campaign(name=campaign_name)
        # Redirect to the new campaign page
        return redirect(url_for("campaign", campaign_name=campaign_name))

    # Add code to retrieve existing campaigns from the database
    existing_campaigns = db_get_campaigns()
    campaigns = [campaign[1] for campaign in existing_campaigns]
    return render_template("campaigns.html", campaigns=campaigns)


@app.route("/<campaign_name>", methods=["GET", "POST"])
def campaign(campaign_name):
    campaign = db_get_campaign(campaign_name=campaign_name)

    if not campaign:
        abort(404)

    campaign_id, campaign_name, _ = campaign

    context = get_lead()
    context["campaign"] = campaign_name
    context["campaign_id"] = campaign_id

    if not context:
        return render_template("no_leads.html")

    if request.method == "POST":
        action = request.form.get("action")
        id = request.form.get("id")
        email = request.form.get("email")
        name = request.form.get("name")
        link = request.form.get("link")
        pronoun = request.form.get("pronoun")
        area = request.form.get("area")

        if action == "delete":
            db_delete_link(id=id)
        elif action == "accept":
            db_create_lead(
                email=email,
                name=name,
                domain=link,
                pronoun=pronoun,
                campaign_id=campaign_id,
                area=area,
            )
            db_delete_link(id=id)

        # Get a new lead
        context = get_lead()

        context["campaign"] = campaign_name
        context["campaign_id"] = campaign_id

        return render_template("partials/form.html", **context)

    return render_template("campaign.html", **context)


@app.route("/download-csv/<campaign_id>")
def download_csv(campaign_id):
    leads = db_get_leads(campaign_id)
    csv_content = generate_csv(leads)
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=export.csv"},
    )


if __name__ == "__main__":
    app.run(debug=True)
