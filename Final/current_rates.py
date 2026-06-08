import requests as rq

def currency_rate():
    url = "https://open.er-api.com/v6/latest/TWD"

    try:
        response = rq.get(url, timeout=5)
        response.raise_for_status
        data = response.json()

        if data.get("result") == "success":
            return data.get("rates", {})
        return{}
    except Exception as e: 
        print(f"Network Connection or API Failure: {e}")
        return {}