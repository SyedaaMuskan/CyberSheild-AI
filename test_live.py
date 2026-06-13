import requests
import json

url = "https://cybershield-backend.graytree-5e13f588.eastus.azurecontainerapps.io/api/analyze"
code = """
def calculate_discount(price, discount_percent):
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Discount must be between 0 and 100")
    final_price = price * (1 - (discount_percent / 100))
    return round(final_price, 2)
"""

res = requests.post(url, json={"code": code})
print(json.dumps(res.json(), indent=2))
