import requests
from bs4 import BeautifulSoup
import re
import time


def get_hearing_detail_raw(url):
    response = requests.get(url, verify=False)
    return response.text


def get_field_value(parent_el, field_regex):
    field_value = parent_el.find_all("div", class_="hearing-item")
    for field in field_value:
        label = field.find("div", class_="label")
        if label and re.search(field_regex, label.get_text(), re.IGNORECASE):
            text = field.find("div", class_="text")
            return text.get_text().strip() if text else None
    return None


def parse_party_el(party_el):
    fields = party_el.find_all("div", class_="hearing-item")
    role_el, name_el = fields[0].find("div", class_="label"), fields[0].find("div", class_="text")
    representation_el = fields[1].find("div", class_="text") if len(fields) > 1 else None

    return {
        "role": role_el.get_text().strip() if role_el else None,
        "name": name_el.get_text().strip() if name_el else None,
        "representation": representation_el.get_text().strip() if representation_el else None
    }


def parse_hearing_detail(html):
    soup = BeautifulSoup(html, 'html.parser')
    hearing_details_el = soup.find("div", class_="detail-wrapper").find("div", class_="row")
    parties_els = soup.find_all("div", class_="row hearing-party")

    return {
        "nature_of_case": get_field_value(hearing_details_el, r"^Nature of case$"),
        "hearing_type": get_field_value(hearing_details_el, r"^Hearing type$"),
        "charge_number": get_field_value(hearing_details_el, r"^Charge number$"),
        "offence_description": get_field_value(hearing_details_el, r"^Offence description$"),
        "hearing_outcome": get_field_value(hearing_details_el, r"^Hearing outcome$"),
        "parties": [parse_party_el(el) for el in parties_els]
    }


def populate_hearing_data(hearings):
    populated_data = []
    for hearing in hearings:
        link = hearing['link']
        try:
            detail_raw = get_hearing_detail_raw(link)
            parsed_details = parse_hearing_detail(detail_raw)
            populated_data.append({**hearing, **parsed_details})
            print(link)
        except Exception as e:
            print(f"Caught exception: {e} {link}")
    return populated_data
