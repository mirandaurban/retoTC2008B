import requests
import json

url = "http://10.49.12.39:5000/api/"
endpoint = "attempt"

data = {
    "year" : 2025,
    "classroom" : 301,
    "name" : "Estrellas",
    "current_cars": 50,
    "total_arrived": 10,
    "attempt_number": 10
}

headers = {
    "Content-Type": "application/json"
}

response = requests.post(url+endpoint, data=json.dumps(data), headers=headers)

print(f"Data: {data}")
print("Request " + "successful" if response.status_code == 200 else "failed", "Status code:", response.status_code)
print("Response:", response.json())