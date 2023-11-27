from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    abort,
    Response,
    flash,
)
from jinja2 import Template

from database import (
    db_get_lead,
    db_get_leads,
    db_create_lead,
    db_create_sent,
    db_delete_link,
    db_create_campaign,
    db_get_campaign,
    db_get_campaigns,
    db_delete_leads,
)

from schema import Link

from utils import generate_csv

app = Flask(__name__, static_folder="content")

app.secret_key = "1234"

# TODO Deleting a link should also delete associated content
# TODO Done write "None" in the field, just let them be empty, and make sure to validate its not empty when being submitted
# TODO In form show lead count + total link count
# TODO Mulighed for at tilføje lead til en anden liste
# TODO Would be nice with stats about links: Remaining links, ready links etc.


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


@app.route("/email-form", methods=["GET", "POST"])
def email_form():
    context = get_lead()

    with open("templates/emails/email.txt", "r", encoding="utf-8") as file:
        email_template = file.read()

    jinja_template = Template(email_template)
    email_content = jinja_template.render(**context)

    context["email_subject"] = "Et par ideer"
    context["email_content"] = email_content

    if not context:
        return render_template("no_leads.html")

    if request.method == "POST":
        action = request.form.get("action")
        id = request.form.get("id")

        if action == "delete":
            db_delete_link(id=id)

        if action == "sent":
            db_delete_link(id=id)
            db_create_sent(domain=context["link"])

        # Get a new lead
        context = get_lead()

        jinja_template = Template(email_template)
        email_content = jinja_template.render(**context)

        context["email_subject"] = "Et par ideer"
        context["email_content"] = email_content

        return render_template("partials/email-form.html", **context)

    return render_template("email.html", **context)


def get_campaign_context(campaign):
    campaign_id, campaign_name, _ = campaign

    context = get_lead()

    if not context:
        return None
    # All campaigns
    existing_campaigns = db_get_campaigns()
    campaigns = [
        (campaign[0], campaign[1])
        for campaign in existing_campaigns
        if campaign[0] != campaign_id
    ]

    context["campaign"] = campaign_name
    context["campaign_id"] = campaign_id
    context["campaigns"] = campaigns

    return context


@app.route("/<campaign_name>", methods=["GET", "POST"])
def campaign(campaign_name):
    campaign = db_get_campaign(campaign_name=campaign_name)

    campaign_id = campaign[0]

    if not campaign:
        abort(404)

    context = get_campaign_context(campaign=campaign)

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
        selected_campaign_id = request.form.get("campaign")

        if action == "delete":
            db_delete_link(id=id)
        elif action == "accept":
            # If alternative campaign has been selected
            if selected_campaign_id:
                campaign_id = selected_campaign_id

            db_create_lead(
                email=email,
                name=name,
                domain=link,
                pronoun=pronoun,
                campaign_id=campaign_id,
                area=area,
            )

            db_delete_link(id=id)

        context = get_campaign_context(campaign=campaign)

        # Check if context is None
        if context is not None:
            return render_template("partials/form.html", **context)
        else:
            return render_template("partials/form.html")

    return render_template("campaign.html", **context)


@app.route("/download-csv/<campaign_id>")
def download_csv(campaign_id):
    # TODO Check for sent
    leads = db_get_leads(campaign_id)
    csv_content = generate_csv(leads)
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=export.csv"},
    )


@app.route("/delete-leads/<campaign_id>", methods=["POST"])
def delete_leads(campaign_id):
    campaign = db_get_campaign(campaign_id=campaign_id)

    if not campaign:
        abort(404)

    campaign_name = campaign[1]

    if request.method == "POST":
        delete = request.form.get("delete")

        if delete == "delete":
            db_delete_leads(campaign_id=campaign_id)
            flash("Leads deleted successfullu", "success")
        else:
            flash('You need to write "delete"', "danger")

        return redirect(url_for("campaign", campaign_name=campaign_name))


if __name__ == "__main__":
    app.run(debug=True)
