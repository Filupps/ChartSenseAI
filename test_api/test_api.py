import requests
import json

with open("138.png", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/predict",
        files={"file": ("138.png", f, "image/png")}
    )

print(f"Status: {response.status_code}")

if response.status_code != 200:
    print(f"Error: {response.text}")
else:
    data = response.json()
    algorithm = data.get("algorithm", {})
    
    with open("algorithm.json", "w", encoding="utf-8") as f:
        json.dump(algorithm, f, ensure_ascii=False, indent=2)
    print("Сохранено в algorithm.json")