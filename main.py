import requests
import pushover
import time


def get_restaurants_by_city(city: str, page: int) -> list:
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }
    url = f"https://api.neotaste.com/cities/{city}/restaurants/?sortBy?recommended&page={page}"
    response = requests.get(url, headers=headers)
    restaurants = response.json()["data"]
    for restaurant in restaurants:
        restaurant["url"] = (
            f"https://neotaste.com//restaurants/{city}/{restaurant['slug']}"
        )
    return restaurants


def get_special_deals(restaurants: list) -> list:
    deals = []
    for restaurant in restaurants:
        for deal in restaurant["deals"]:
            deal["restaurant_name"] = restaurant["name"]
            deal["restaurant_url"] = restaurant["url"]
            deals.append(deal)
    special_deals = [deal for deal in deals if "🌟" in deal["name"]]
    return special_deals


def get_deal_availability(deal: dict) -> dict:
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }
    url = f"https://api.neotaste.com/restaurants/deals/{deal['uuid']}/timeframes"
    while True:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            timeframeGroups = [
                day
                for day in response.json()["data"]
                if day["numberOfAvailableDeals"] > 0
            ]
            deal["timeframeGroups"] = timeframeGroups
            deal["status"] = "available" if len(timeframeGroups) > 0 else "unavailable"
            break
        else:
            print("Retrying")
    return deal


def get_deal_availabilities(deals: list) -> list:
    return [get_deal_availability(deal) for deal in deals]


def get_available_deals(deals: list) -> list:
    deal_availabilities = get_deal_availabilities(deals)
    return [
        deal_availability
        for deal_availability in deal_availabilities
        if deal_availability["status"] == "available"
    ]


def get_deal_by_uuid(available_deals: list, deal_uuid: str) -> list:
    return [deal for deal in available_deals if deal_uuid == deal["uuid"]]


def get_deal_quantity(deal: dict) -> int:
    return sum(
        [timeframe["numberOfAvailableDeals"] for timeframe in deal["timeframeGroups"]]
    )


def compare_deals(deal1, deal2):
    return deal1["name"] == deal2["name"]


def monitor_special_deals(city: str, sleep_delay: int = 60) -> None:
    first_run = True
    previously_available_deals = []
    while True:
        restaurants = get_restaurants_by_city(city, page=1)
        special_deals = get_special_deals(restaurants)
        currently_available_deals = get_available_deals(special_deals)

        if first_run:
            previously_available_deals = currently_available_deals
            first_run = False

        added_deals = [
            deal
            for deal in currently_available_deals
            if deal["name"]
            not in [
                previous_deal["name"] for previous_deal in previously_available_deals
            ]  # only ping when stock turns from zero to positive integer
        ]

        if added_deals:
            print(f"[NeoTaste] Change detected, pinging {len(added_deals)} deals...")
            for deal in added_deals:
                message = f"{get_deal_quantity(deal)}x '{deal['name']}' available at {deal['restaurant_name']}\nLink: {deal['restaurant_url']}"
                pushover.send_message_to_users(message)

        previously_available_deals = currently_available_deals
        print(f"[NeoTaste] Nothing changed, sleeping for {sleep_delay}s...")
        time.sleep(sleep_delay)


def main() -> None:
    monitor_special_deals(city="vienna", sleep_delay=60)


if __name__ == "__main__":
    main()
