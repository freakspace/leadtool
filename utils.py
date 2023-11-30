import io
import csv
from urllib.parse import urlparse


def extract_domain(url):
    if not urlparse(url).scheme:
        url = "http://" + url

    parsed_url = urlparse(url)
    # Extract the domain name (netloc)
    domain = parsed_url.netloc

    # Sometimes, the URL might include www. at the beginning or have a port.
    # You can remove them like this:
    domain = domain.replace("www.", "")
    domain = domain.split(":")[0]  # Removes port number if it exists

    return domain


def generate_csv(leads):
    # Generate CSV in memory
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["id", "email", "name", "domain", "pronoun", "area"])
    cw.writerows(leads)
    output = si.getvalue()
    si.close()
    return output
