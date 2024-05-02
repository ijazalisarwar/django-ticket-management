import json

import requests
from accounts.models import City, State
import json
from accounts.models import City, State


def save_states_and_cities():
    url = "https://parseapi.back4app.com/classes/Uszipcode_US_Zip_Code?limit=1000000000000000000000000000"
    headers = {
        "X-Parse-Application-Id": "d4ssrILiW1vtJ0RjIhJAVEoBtvDDg3hs0rDXJ3eR",
        "X-Parse-REST-API-Key": "wsmNemHrQD20nbUIhWxQN9CmWsd94FZVZ8gJWK4f",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        for entry in data["results"]:
            state_name = entry["State"]
            city_name = entry["Primary_city"]
            state_obj, created_state = State.objects.get_or_create(name=state_name)
            city_obj, created_city = City.objects.get_or_create(
                state=state_obj, name=city_name
            )
            if created_state:
                print(f"Created state: {state_name}")
            if created_city:
                print(f"Created city: {city_name} in state: {state_name}")
    else:
        print(f"Error: {response.status_code}, {response.text}")


def fetch_states_and_cities():
    username = "saadan"
    base_url = "https://secure.geonames.org/"
    state_response = requests.get(
        f"{base_url}childrenJSON?geonameId=6252001&username={username}"
    )
    state_data = state_response.json()
    if "geonames" in state_data:
        states = state_data["geonames"]
        for state in states:
            state_name = state["name"]
            state_geoname_id = state["geonameId"]
            state_obj, created = State.objects.get_or_create(
                geoname_id=state_geoname_id, defaults={"name": state_name}
            )
            city_response = requests.get(
                f"{base_url}childrenJSON?geonameId={state_geoname_id}&username={username}"
            )
            city_data = city_response.json()
            if "geonames" in city_data:
                cities = city_data["geonames"]
                for city in cities:
                    city_name = city["name"]
                    city_obj, created = City.objects.get_or_create(
                        state=state_obj, name=city_name
                    )


def get_states():
    geonames_username = "saadan"
    response = requests.get(
        f"https://secure.geonames.org/childrenJSON?geonameId=6252001&username={geonames_username}"
    )
    if response.status_code == 200:
        states = response.json().get("geonames", [])
        return {state["geonameId"]: state["name"] for state in states}
    else:
        return {}


def import_cities_data():
    help = "Import city and state data from JSON file"

    try:
        with open("static/city_state.json", "r") as file:
            print("Reading JSON file...")
            data = json.load(file)
            results = data.get("results", [])
            print(f"Processing {len(results)} records...")
            for index, item in enumerate(results, start=1):
                state_name = item.get("State", "")
                print("State ", state_name)
                city_name = item.get("Primary_city", "")
                print("city_name ", city_name)
                if state_name and city_name:

                    state_obj, created_state = State.objects.get_or_create(
                        name=state_name
                    )
                    city_obj, created_city = City.objects.get_or_create(
                        state=state_obj, name=city_name
                    )
                    if created_state:
                        print(f"Created state: {state_name}")

                    if created_city:
                        print(f"Created city: {city_name} in state: {state_name}")

                    print(f"Processed {index} records.")

            print("City and state data import completed.")

    except FileNotFoundError:
        print("Error: File not found.")

    except json.JSONDecodeError:
        print("Error: Failed to decode JSON.")

    except Exception as e:
        print(f"An error occurred: {e}")
