from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    abort,
    Response,
    flash,
    session,
)

from database import (
    db_get_lead,
    db_get_leads,
    db_get_all_leads,
    db_delete_all_leads,
    db_create_lead,
    db_create_sent,
    db_delete_link,
    db_create_campaign,
    db_get_campaign,
    db_get_campaigns,
    db_delete_leads,
    db_get_lead_count_from_campaign,
    db_get_one_lead,
    db_update_lead,
    db_get_lead_count_remainder,
    db_get_lead_count,
    db_get_unparsed_links,
    db_get_unscraped_links,
    db_verify_password,
    db_create_worklog,
    db_get_user,
    db_get_worklogs,
)

from schema import Link

from utils import generate_csv

from routes import routes_blueprint

from decorators import login_required

app = Flask(__name__, static_folder="content")

app.register_blueprint(routes_blueprint, url_prefix="/api")

app.secret_key = "1234"


# TODO Deleting a link should also delete associated content
# TODO List of all leads with options to edit each field
# TODO Have AI classify the design from 1 to 10
# TODO When getting links from google sheets, skip whichever link is in sent table
# TODO When feeds is getting parsed, check / skip for sent
# TODO Before exporting a list, check for sent
# TODO Add a delete button to lead list
# TODO Remove aps, /v from name
# TODO Clean up lead vs. link vs. domain
# TODO Add testing
# TODO Create a list of invalid links and check for domain rating.
# TODO Vis link i leadlist
# TODO Aiparser should also check the industry that it conforms with the expectaion
# TODO Categories links when parsing?
# TODO Make it possible to send a list of links instead of one at a time
# TODO Make a function to export all pre-leads, just remove the ones with "none" fields.
# TODO Normalize data None vs none


def get_lead():
    lead: Link = db_get_lead()

    if not lead:
        return None

    context = {
        "id": lead.id,
        "link": lead.link,
        "email": lead.email,
        "name": lead.contact_name,
        "pronoun": lead.pronoun,
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
    campaigns = [
        {"id": campaign[0], "name": campaign[1]} for campaign in existing_campaigns
    ]

    total_unscraped_links = db_get_unscraped_links()
    total_unparsed_links = db_get_unparsed_links()
    total_leads = db_get_lead_count()
    remaining_leads = db_get_lead_count_remainder()

    context = {
        "campaigns": campaigns,
        "total_unscraped_links": total_unscraped_links,
        "total_unparsed_links": len(total_unparsed_links),
        "remaining_leads": remaining_leads,
        "total_leads": total_leads,
    }

    return render_template("campaigns.html", **context)


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
    context["campaign_count"] = db_get_lead_count_from_campaign(campaign_id=campaign_id)
    context["remaining_leads"] = db_get_lead_count_remainder()
    context["campaign_id"] = campaign_id
    context["campaigns"] = campaigns

    return context


@app.route("/<campaign_name>", methods=["GET", "POST"])
@login_required
def campaign(campaign_name):
    username = session["username"]
    user_id = db_get_user(username=username)[0]

    campaign = db_get_campaign(campaign_name=campaign_name)

    if not campaign:
        abort(404)

    campaign_id = campaign[0]

    context = get_campaign_context(campaign=campaign)

    if not context:
        return render_template("no_leads.html", campaign_id=campaign_id)

    if request.method == "POST":
        action = request.form.get("action")
        id = request.form.get("id")
        email = request.form.get("email")
        name = request.form.get("name")
        domain = request.form.get("link")
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
                domain=domain,
                pronoun=pronoun,
                campaign_id=campaign_id,
                area=area,
            )

            db_create_sent(domain=domain)
            db_delete_link(id=id)
        print(f"Adding worklog: {user_id}, {domain}")
        db_create_worklog(user_id=user_id, domain=domain)

        context = get_campaign_context(campaign=campaign)

        # Check if context is None
        if context is not None:
            return render_template("partials/form.html", **context)
        else:
            return render_template("partials/form.html")

    return render_template("campaign.html", **context)


@app.route("/leads/<campaign_id>", methods=["GET", "POST"])
@login_required
def leads(campaign_id):
    campaign = db_get_campaign(campaign_id=campaign_id)

    if not campaign:
        abort(404)

    leads_data = db_get_leads(campaign_id=campaign_id)

    if not leads_data:
        return render_template("no_leads.html", campaign_id=campaign_id)

    # Convert each lead tuple to a dictionary
    leads = []
    for lead in leads_data:
        lead_dict = {
            "id": lead[0],
            "email": lead[1],
            "name": lead[2],
            "domain": lead[3],
            "pronoun": lead[4],
            "area": lead[5],
        }
        leads.append(lead_dict)

    context = {"leads": leads, "campaign_id": campaign_id}

    if request.method == "POST":
        lead_id = request.form.get("lead_id")
        email = request.form.get("email")
        name = request.form.get("name")
        domain = request.form.get("domain")
        pronoun = request.form.get("pronoun")
        updated_campaign_id = request.form.get("campaign_id")
        area = request.form.get("area")
        print(f"Updating campaign id: {updated_campaign_id}")
        db_update_lead(
            id=lead_id,
            email=email,
            name=name,
            domain=domain,
            pronoun=pronoun,
            campaign_id=updated_campaign_id,
            area=area,
        )

        updated_lead_data = db_get_one_lead(lead_id=lead_id)

        updated_lead = {
            "id": updated_lead_data[0],
            "email": updated_lead_data[1],
            "name": updated_lead_data[2],
            "domain": updated_lead_data[3],
            "pronoun": updated_lead_data[4],
            # "campaign_id": updated_lead_data[5],
            "area": updated_lead_data[6],
        }

        context = {"lead": updated_lead, "campaign_id": campaign_id}

        return render_template("partials/lead_form.html", **context)

    return render_template("campaign_leads.html", **context)


@app.route("/worklog", methods=["GET"])
@login_required
def worklog():
    username = session["username"]
    user = db_get_user(username=username)
    worklogs_data = db_get_worklogs(user_id=user[0])

    if not worklogs_data:
        return render_template("no_worklogs.html")

    # Convert each lead tuple to a dictionary
    worklogs = []
    total_pay = 0
    for log in worklogs_data:
        worklog_dict = {"timestamp": log[3], "domain": log[2], "pay": user[5]}
        worklogs.append(worklog_dict)
        total_pay += float(user[5])

    context = {"worklogs": worklogs, "total_pay": total_pay}

    return render_template("worklogs.html", **context)


@app.route("/download-csv/<campaign_id>")
def download_csv(campaign_id):
    # TODO Check for sent
    leads = db_get_leads(campaign_id)
    csv_content = generate_csv(
        leads, ["id", "email", "name", "domain", "pronoun", "area"]
    )
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=export.csv"},
    )


@app.route("/dump-all", methods=["GET"])
def dump_all():
    leads = db_get_all_leads()
    csv_content = generate_csv(leads, ["domain", "email", "name", "pronoun", "area"])
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=export.csv"},
    )


@app.route("/delete-all", methods=["POST"])
def delete_all():
    if request.method == "POST":
        delete = request.form.get("delete")

        if delete == "delete":
            db_delete_all_leads()
            flash("Leads deleted successfully", "success")
        else:
            flash('You need to write "delete"', "danger")

        return redirect(url_for("home"))


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
            flash("Leads deleted successfully", "success")
        else:
            flash('You need to write "delete"', "danger")

        return redirect(url_for("campaign", campaign_name=campaign_name))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if db_verify_password(username, password):
            session["username"] = username
            return redirect(url_for("home"))
        return "Invalid username or password"

    return render_template("login.html")


# Logout page
@app.route("/logout")
@login_required
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
