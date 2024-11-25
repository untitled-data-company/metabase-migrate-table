import requests

METABASE_API_KEY = "REPLACE_ME"
BASE_URL = "https://my_metabase_instance_url/api"
headers = {
    "Content-Type": "application/json",
    "x-api-key": METABASE_API_KEY,
}

if METABASE_API_KEY == "change_me":
    raise ValueError("METABASE_API_KEY needs to be updated!")


def call_metabase_api(query_endpoint: str, method: str = "GET", data: str = ""):
    if method == "PUT":
        response = requests.put(
            f"{BASE_URL}/{query_endpoint}", headers=headers, json=data
        )
    if method == "POST":
        response = requests.post(
            f"{BASE_URL}/{query_endpoint}", headers=headers, data=data
        )
    else:
        response = requests.get(f"{BASE_URL}/{query_endpoint}", headers=headers)
    if response.status_code in [200, 202]:
        return response.json()
    else:
        print(
            "!!!! ERROR:", response.status_code, response.text[:30].replace("\n", " ")
        )
        return None


def get_source_table(query):
    return query.get("source-query", query).get("source-table", None)


def get_field_name(field_id):
    query_endpoint = f"field/{field_id}"
    return call_metabase_api(query_endpoint)["name"]


def modify_field_values(data, table):
    # Check if the data is a list
    if isinstance(data, list):
        # If the current list matches the pattern ["field", <number>, <any>]
        if (
            len(data) == 3
            and data[0] == "field"
            and isinstance(data[1], (int, float))
            and table.is_field_in_old_table(data[1])
        ):
            new_field_name = get_field_name(data[1])
            data[1] = table.new_fields[new_field_name]  # Modify the field id
        else:
            # Otherwise, recursively check each element of the list
            for i in range(len(data)):
                modify_field_values(data[i], table)
    elif isinstance(data, dict):
        # If it's a dictionary, iterate over its values
        for key in data:
            modify_field_values(data[key], table)
    return data
