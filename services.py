import requests


def update_link_record(link_id: int, email, contact_name, industry, city, area, parsed):
    url = f"http://localhost:5000/api/update_link/{link_id}"

    data = {
        "email": email,
        "contact_name": contact_name,
        "industry": industry,
        "city": city,
        "area": area,
        "parsed": parsed,
    }

    response = requests.post(url, json=data)

    print(response)


def check_sent(domain: str = None, email: str = None):
    url = f"http://localhost:5000/api/check_sent"

    data = {"domain": domain, "email": email}

    response = requests.post(url, json=data)
    if response.status_code == 200:
        data = response.json()
        return data["sent"]
    else:
        raise Exception("Bad request")
