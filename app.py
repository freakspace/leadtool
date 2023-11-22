from datetime import datetime
from flask import Flask, render_template, request, jsonify
from jinja2 import Template

from database import db_get_lead, db_create_email_event, db_get_events, get_next_email_event_date

from mailgun import schedule_email

from schema import Link

app = Flask(__name__, static_folder='content')

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
        "screenshot": f"content/{lead.link}.png",
        "email_subject": "Et par ideer",
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

    deliverytime = None

    if request.method == "POST":
        action = request.form.get("action")

        email = request.form.get("email")
        email_subject = request.form.get("email_subject")
        email_content = request.form.get("email_content")

        if action == "reject":
            # Handle the reject action
            qc_result = 0
        elif action == "sent":
            qc_result = 1
            deliverytime = datetime.now()
        elif action == "schedule":
            # TODO Remember to change to_email
            #try:
            deliverytime = schedule_email(
                to_email="hej@emilnielsen.com",
                subject=email_subject,
                text=email_content
            )
            qc_result = 1
            """ except Exception as e:
                return jsonify(message=str(e)), 400 """

        #  Create email event
        db_create_email_event(
            link_id=context["id"],
            qc_result=qc_result,
            email_content=email_content,
            deliverytime=deliverytime,
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
