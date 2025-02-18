import logging
from curl_cffi import requests
from time import sleep
from rich.logging import RichHandler
from config import *

FORMAT = "%(message)s"
logging.basicConfig(level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])
log = logging.getLogger("rich")

BASE = "https://discord.com"

def open_session():
    session = requests.Session(impersonate="chrome120")
    session.cookies = session.get(BASE).cookies

    session.headers["Authorization"] = USER_TOKEN
    session.headers["Origin"] = BASE
    session.headers["Referer"] = f"{BASE}/channels/@me"

    return session

def fetch_messages(limit, before=None):
    session = open_session()
    url = f"{BASE}/api/v9/channels/{CHANNEL_ID}/messages?limit={limit}"

    if before:
        url = f"{BASE}/api/v9/channels/{CHANNEL_ID}/messages?limit={limit}&before={before}"

    response = session.request("GET", url)
    return response

def delete_message(message_id, channel_id):
    session = open_session()
    url = f"{BASE}/api/v9/channels/{channel_id}/messages/{message_id}"

    while True:
        response = session.request("DELETE", url)
        
        if response.status_code == 429:
            retry_after = response.json()["retry_after"]
            log.warning(f"Rate limit hit. Retrying after {retry_after} seconds")
            sleep(float(retry_after))
        elif response.status_code in {200, 204}:
            log.info(f"Successfully deleted message: {message_id}"); break
        else:
            if response.json()["code"] == 50021: return
            log.error(f"Failed ({response.status_code}) to delete message: {message_id}"); break

def main():
    limit = 100
    before = None
    all_messages = []

    while True:
        response = fetch_messages(limit, before)
        if response.status_code != 200:
            log.error(f"Failed ({response.status_code}) while fetching messages")
            break

        messages = response.json()
        if not messages: break

        for message in messages:
            if message["author"]["id"] == str(USER_ID):
                all_messages.append(message)

        before = messages[-1]["id"]

    log.info(f"Fetched {len(all_messages)} messages sent by you")
    for message in all_messages:
        delete_message(message["id"], CHANNEL_ID)

if __name__ == "__main__":
    main()
