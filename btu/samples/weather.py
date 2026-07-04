import requests


def get_current_weather(latitude, longitude):
	url = "https://api.open-meteo.com/v1/forecast"
	params = {
		"latitude": latitude,
		"longitude": longitude,
		"current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
		"temperature_unit": "fahrenheit",
		"wind_speed_unit": "mph",
		"timezone": "auto",
	}
	response = requests.get(url, params=params)
	response.raise_for_status()
	return response.json()
