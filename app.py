from datetime import datetime
from flask import Flask, render_template, request, jsonify
from jinja2 import Template

from database import db_get_lead, db_create_email_event, db_get_events

from mailgun import schedule_email

from schema import Link

app = Flask(__name__)

# TODO Delete lead / Skip lead
# TODO Add copy buttons to template
# TODO Option to add lists (as in industries)
# TODO Option to move lead from list to list


def get_lead():
    lead: Link = db_get_lead()

    if not lead:
        return None

    with open("templates/emails/email.txt", "r", encoding="utf-8") as file:
        email_template = file.read()

    context = {
        "id": lead.id,
        "link": lead.link,
        "email": lead.email,
        "name": lead.contact_name,
        "industry": lead.industry,
        "city": lead.city,
        "area": lead.area,
    }

    # Render the template content with the updated context
    jinja_template = Template(email_template)
    email_content = jinja_template.render(**context)
    context["email_content"] = email_content

    return context


@app.route("/", methods=["GET", "POST"])
def home():
    context = get_lead()

    if not context:
        return render_template("no_leads.html")

    contacted_at = None

    if request.method == "POST":
        action = request.form.get("action")

        email = request.form.get("email")
        email_content = request.form.get("email_content")

        if action == "reject":
            # Handle the reject action
            qc_result = 0
        elif action == "sent":
            qc_result = 1
            contacted_at = datetime.now()
        elif action == "schedule":
            # TODO Get random domain
            # TODO Remember to change to_email
            request = schedule_email(
                domain="sandbox3409de04326a4d1cbf4b0fe0c754fcea.mailgun.org",
                from_email="Emil Nielsen <emil@sandbox3409de04326a4d1cbf4b0fe0c754fcea.mailgun.org>",
                to_email="hej@emilnielsen.com",
                subject="Et par ideer",
                text=email_content,
            )

            qc_result = 1
            contacted_at = datetime.now()
            if request != 200:
                return jsonify(message=request.text), 400

        #  Create email event
        db_create_email_event(
            link_id=context["id"],
            qc_result=qc_result,
            email_content=email_content,
            contacted_at=contacted_at,
        )

        # Get a new lead
        context = get_lead()

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
