from requests import get
from bs4 import BeautifulSoup


def get_domains():
    r = get("https://www.1secmail.com/api/v1/?action=getDomainList")
    if r.status_code == 200:
        return eval(r.text)
    return []


def get_mails(email):
    username, domain = email.split("@")
    api_uri = f"https://www.1secmail.com/api/v1/?action=getMessages&login={username}&domain={domain}"
    resp = get(api_uri)
    if resp.status_code != 200:
        return (None, "Server down!")
    try:
        mails = eval(resp.text)
    except Exception as exc:
        print("Error parsing mailbox: %s", exc)
        return (None, "Error parsing mailbox: %s" % exc)
    return (mails, None)


def get_mail_data(username, domain, mail_id):
    if not username or not domain:
        return None
    api_url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={username}&domain={domain}&id={mail_id}"
    r = get(api_url)
    if r.status_code == 200:
        return r.json()
    return None


def remove_html_tags(html_content):
    """
    Remove all HTML tags from the given HTML content and return plain text.

    :param html_content: A string containing HTML content
    :return: A string with HTML tags removed
    """
    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    return text
