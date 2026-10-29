
import os
import requests
from dotenv import load_dotenv

# Load the API key from .env
load_dotenv()

api_key = os.getenv("OMDB_API_KEY")

if not api_key:
    print("API key not found. Check your .env file.")
else:
    url = "https://www.omdbapi.com/"
    params = {
        "apikey": api_key,
        "t": "Toy Story",
        "type": "movie"
    }

    response = requests.get(url, params=params, timeout=15)
    data = response.json()

    if data.get("Response") == "True":
        print("API connection successful!")
        print("Title:", data.get("Title"))
        print("Year:", data.get("Year"))
        print("Director:", data.get("Director"))
    else:
        print("API request failed:", data.get("Error"))
