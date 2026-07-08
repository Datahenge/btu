"""Sample BTU task: fetch the current weather from the free Open-Meteo API.

This is the canonical BTU demo function. It deliberately does **two** things so you
can see how BTU captures both output channels of a task:

* Anything the function **prints** to stdout is stored in the BTU Task Log's
  *Standard Output* field.
* Whatever the function **returns** is stored in the BTU Task Log's
  *Result Message* field.

It runs with no arguments (defaults to Vancouver, WA), so you can create a BTU Task
pointing at ``btu.samples.weather.get_current_weather`` and run it immediately.
"""

import requests

# Open-Meteo uses WMO weather codes. This is a friendly subset for the demo.
WEATHER_CODES = {
	0: "clear sky",
	1: "mainly clear",
	2: "partly cloudy",
	3: "overcast",
	45: "fog",
	48: "depositing rime fog",
	51: "light drizzle",
	53: "moderate drizzle",
	55: "dense drizzle",
	61: "light rain",
	63: "moderate rain",
	65: "heavy rain",
	71: "light snow",
	73: "moderate snow",
	75: "heavy snow",
	80: "rain showers",
	81: "moderate rain showers",
	82: "violent rain showers",
	95: "thunderstorm",
	96: "thunderstorm with hail",
}


def get_current_weather(latitude=45.6387, longitude=-122.6615, label="Vancouver, WA"):
	"""Fetch current conditions, print a human summary, and return a compact dict.

	Args:
		latitude: Decimal degrees. Defaults to Vancouver, WA.
		longitude: Decimal degrees. Defaults to Vancouver, WA.
		label: Friendly place name used in the printed summary.

	Returns:
		dict with ``location``, ``temperature_f``, ``humidity_pct``, ``wind_mph``,
		and ``conditions`` — this becomes the Task Log *Result Message*.
	"""
	response = requests.get(
		"https://api.open-meteo.com/v1/forecast",
		params={
			"latitude": latitude,
			"longitude": longitude,
			"current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
			"temperature_unit": "fahrenheit",
			"wind_speed_unit": "mph",
			"timezone": "auto",
		},
		timeout=30,
	)
	response.raise_for_status()
	current = response.json()["current"]

	temperature_f = current["temperature_2m"]
	humidity_pct = current["relative_humidity_2m"]
	wind_mph = current["wind_speed_10m"]
	conditions = WEATHER_CODES.get(current["weather_code"], "unknown conditions")

	# --> Standard Output in the BTU Task Log
	print(
		f"Current weather for {label}: {temperature_f}°F, {conditions}, "
		f"humidity {humidity_pct}%, wind {wind_mph} mph."
	)

	# --> Result Message in the BTU Task Log
	return {
		"location": label,
		"temperature_f": temperature_f,
		"humidity_pct": humidity_pct,
		"wind_mph": wind_mph,
		"conditions": conditions,
	}
