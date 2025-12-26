from datetime import datetime
import requests
import json

from flask import current_app

from . import logging

# False or date of the last rate limit
is_rate_limited = False

def get_possible_queries(is_admin: bool) -> int:
    """Returns the number of queries a user can do"""
    num_queries = current_app.config["MAX_ONLINE_QUERIES"] if not is_admin else 10

    if (
        current_app.config["GOOGLE_API_KEY"] == "" or
        current_app.config["GOOGLE_SEARCH_ENGINE_ID"] == "" or
        is_rate_limited == datetime.today()
    ):
        return 0
    return min(num_queries, 10)

def search(query: str, num_queries: int):
    params = {
        "fileType": "pdf",
        "safe": "active",
        "num": min(num_queries, 10),
        "q": query + "partition",
        "key": current_app.config["GOOGLE_API_KEY"],
        "cx": current_app.config["GOOGLE_SEARCH_ENGINE_ID"]
    }
    resp = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
    if resp.status_code != 200:
        logging.log(
            (resp.status_code, query, json.dumps(json.loads(resp.text))), logging.LogEntry.GOOGLE_ERROR
        )

        # This might also be a misconfiguration, but we block further requests
        global is_rate_limited
        is_rate_limited = datetime.today()

        return []

    items = [item["link"] for item in json.loads(resp.text).get("items", [])]
    return items[:min(len(items), num_queries)]
