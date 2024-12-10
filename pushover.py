import requests
import urllib.parse
import time
import os
from dotenv import load_dotenv
import json


def read_env():
    load_dotenv(override=True)
    global APP_TOKEN
    global USERS
    APP_TOKEN = os.environ.get("APP_TOKEN")
    USERS = json.loads(os.environ.get("USERS"))


def send_message_to_user(user_name, user_token, message, timestamp=None) -> None:
    if timestamp is not None:
        current_unix_timestamp = time.time()
        if timestamp > current_unix_timestamp:
            sleep_duration = timestamp - current_unix_timestamp
            print(f"[PUSHOVER][{timestamp}] Sleeping {sleep_duration}s ...")
            time.sleep(sleep_duration)

    while True:
        try:
            params = {
                "token": APP_TOKEN,
                "user": user_token,
                "message": message,
                "priority": "-1",
                "expire": "600",
                "retry": "30",
            }
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            payload = urllib.parse.urlencode(params)
            response = requests.post(
                "https://api.pushover.net/1/messages.json",
                headers=headers,
                data=payload,
                timeout=3,
            )
            if response.status_code == 200:
                print(
                    f"[PUSHOVER] {user_name}: Successfully sent message: '{message}'."
                )
                break
            elif response.status_code == 404:
                print(
                    f"[PUSHOVER] {user_name}: Error sending message: '{message}', retrying..."
                )
                continue
        except Exception as e:
            print(f"[PUSHOVER] {user_name}: Exception {e}")
            continue


def send_message_to_users(message, timestamp=None) -> None:
    read_env()
    for user_name, user_token in USERS.items():
        send_message_to_user(user_name, user_token, message, timestamp)


if __name__ == "__main__":
    send_message_to_users(message="Example Message")
