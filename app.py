from flask import Flask, render_template, request, redirect, url_for

from database import (
    db_get_lead,
    db_create_lead,
    db_delete_link,
    db_create_campaign,
    db_get_campaign,
    db_get_campaigns,
)

from schema import Link

app = Flask(__name__, static_folder="content")

# TODO Delete lead / Skip lead
# TODO Option to add lists (as in industries)
# TODO Option to move lead from list to list
# TODO Importing a new list should check for dublicate emails
# TODO 1. Create new campaign, 2. Upload list, 3. Define template, 4. Define keywords (such as industry), 5. Define timeframe, domains, frequency etc.
# TODO Make domain a link
# TODO Add screenshot


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
    campaign_id, campaign_name, _ = db_get_campaign(campaign_name=campaign_name)

    if not campaign:
        print("No campaign..")

    context = get_lead()
    context["campaign"] = campaign_name

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

        return render_template("partials/form.html", **context)

    return render_template("index.html", **context)


@app.route("/events", methods=["GET", "POST"])
def events():
    events = db_get_events()

    if not events:
        return render_template("no_events.html")

    if request.method == "POST":
        pass

    return render_template("events.html", events=events)


if __name__ == "__main__":
    app.run(debug=True)
