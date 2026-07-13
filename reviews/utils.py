import requests

def fetch_rawg_data(slug):
    url = f"https://api.rawg.io/api/games/{slug}?key=27f6e1ae5c414169b86c67ef36f312f8"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None
