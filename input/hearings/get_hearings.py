import re
import requests
from bs4 import BeautifulSoup
from populate_hearing_data import populate_hearing_data
import json
from datetime import datetime, timedelta
import math
import urllib3
urllib3.disable_warnings()

URL = "https://www.judiciary.gov.sg/hearing-list/GetFilteredList"
JSON_FILE = "data/hearings.json"

# Set the start and end dates when the script is first run
selected_start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
selected_end_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def make_request_body(page=0):
    return {
        "model": {
            "CurrentPage": page,
            "SelectedCourtTab": "",
            "SearchKeywords": "",
            "SearchKeywordsGrouping": "",
            "SelectedCourt": "",
            "SelectedLawFirms": [],
            "SelectedJudges": [],
            "SelectedHearingTypes": [],
            "SelectedStartDate": selected_start_date,
            "SelectedEndDate": selected_end_date,
            "SelectedPageSize": 500,
            "SelectedSortBy": ""
        }
    }


def get_hearing_list_page_raw(page):
    response = requests.post(URL, json=make_request_body(page), verify=False)
    content = json.loads(response.text)
    return BeautifulSoup(content['listPartialView'], 'html.parser')


def get_hearing_type(html_el):
    selection = html_el.select(".hearing-metadata .hearing-type")
    return selection[0].get_text().strip() if selection else None


def format_timestamp(timestamp):
    return datetime.strptime(timestamp, "%d %b %Y, %I:%M %p").isoformat()


def parse_hearing_element(html_el):
    hearing_metadata_els = html_el.select(".hearing-metadata .metadata-wrapper .metadata")
    return {
        "title": html_el.attrs['title'],
        "link": "https://www.judiciary.gov.sg" + html_el.attrs['href'],
        "type": get_hearing_type(html_el),
        "reference": hearing_metadata_els[1].get_text().strip() if len(hearing_metadata_els) > 1 else None,
        "timestamp": format_timestamp(hearing_metadata_els[0].get_text().strip()),
        "venue": html_el.select_one(".hearing-item-wrapper .text").get_text().strip(),
        "coram": html_el.select(".hearing-item-wrapper .text")[1].get_text().strip()
    }


def parse_hearing_list_html(soup):
    return [parse_hearing_element(el) for el in soup.select("a.list-item")]


def get_pagination_status(soup):
    pagination_status = soup.select_one(".pagination-summary")
    if pagination_status:
        total_count = int(re.search(r"Showing results 1-500 of (\d+)", pagination_status.get_text()).group(1))
        return math.ceil(total_count / 500)
    return 0


def get_hearing_list():
    first_page_html = get_hearing_list_page_raw(0)
    additional_pages_count = get_pagination_status(first_page_html)
    print(f"pages count {additional_pages_count}")
    hearings = parse_hearing_list_html(first_page_html)
    for page in range(1, additional_pages_count):
        page_html = get_hearing_list_page_raw(page)
        hearings.extend(parse_hearing_list_html(page_html))
    return hearings


def remove_duplicates(hearings):
    unique_hearings = {}
    for hearing in hearings:
        unique_hearings[hearing['link']] = hearing
    return list(unique_hearings.values())


def main():
    hearings = get_hearing_list()
    # populate_hearing_data would be a separate function or module to process 'hearings' data
    processed_data = remove_duplicates(populate_hearing_data(hearings))
    with open(JSON_FILE, 'w') as f:
        json.dump(processed_data, f)


if __name__ == "__main__":
    main()
