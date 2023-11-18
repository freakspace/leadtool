from datetime import datetime
from flask import Flask, render_template, request
from jinja2 import Template

from database import db_get_lead, db_create_email_event

from schema import Link

app = Flask(__name__)


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

    if request.method == "POST":
        action = request.form.get("action")

        email_content = request.form.get("email_content")

        if action == "accept":
            # Handle the accept action
            qc_result = 1
        elif action == "reject":
            # Handle the reject action
            qc_result = 0

        #  Create email event
        db_create_email_event(
            link_id=context["id"], qc_result=qc_result, email_content=email_content
        )

        # Get a new lead
        context = get_lead()

        return render_template("partials/form.html", **context)

    return render_template("index.html", **context)


if __name__ == "__main__":
    app.run(debug=True)
