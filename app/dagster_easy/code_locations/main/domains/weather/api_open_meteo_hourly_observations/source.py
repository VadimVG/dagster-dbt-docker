import logging

import dlt
from dlt.sources.helpers import requests

logger = logging.getLogger(__name__)

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
FIELDS = ["temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m"]
CITIES = {
    "moscow": (55.75, 37.62),
    "saint_petersburg": (59.94, 30.31),
    "novosibirsk": (55.03, 82.92),
}


@dlt.resource(name="hourly_observations")
def hourly_observations(past_days: int):
    for city, (latitude, longitude) in CITIES.items():
        response = requests.get(
            FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "hourly": ",".join(FIELDS),
                "past_days": past_days,
                "forecast_days": 0,
                "timezone": "UTC",
            },
            timeout=30,
        )
        response.raise_for_status()
        hourly = response.json()["hourly"]
        logger.info("Fetched %s rows for %s", len(hourly["time"]), city)
        for index, time in enumerate(hourly["time"]):
            yield {"city": city, "time": time, **{f: hourly[f][index] for f in FIELDS}}
