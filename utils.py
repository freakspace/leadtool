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
