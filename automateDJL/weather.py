import json
import requests
from datetime import datetime, timezone, tzinfo
from datetime import timezone
import logging


class Weather:
    # Determine how much to charge battery at cheap rate based
    # how much sun there is likely to be the next day.
    # Must run this the day before to set the giv controller config
    # prior to cheap rate energy period

    def __init__(self, gpslat, gpslong, apitoken):
        self.weatherAPIURL = (
            "https://api.openweathermap.org/data/2.5/onecall?lat="
            + gpslat
            + "&lon="
            + gpslong
            + "&appid="
            + apitoken
            + "&units=metric&exclude=current,minutely,daily,alerts"
        )
        self.weatherJSON = []
        self.logger = logging.getLogger("automateDJL")

    def getForecast(self):
        # request the hourly weather forecast for tomorrow
        self.logger.debug("get weather forecast")
        response = requests.get(self.weatherAPIURL)
        self.weatherJSON = json.loads(response.text)
        return self.weatherJSON

    def cloudTomorrow(self):

        if len(self.weatherJSON) == 0:
            self.getForecast()

        now = datetime.today()
        today = now.day
        clouds = []

        for hour in self.weatherJSON["hourly"]:
            dt = datetime.fromtimestamp(hour["dt"])
            nextDay = 0

            if dt.day != today:
                nextDay = dt.day
                # print("dt.hr {} cld {}".format(dt.hour, hour["clouds"]))
                clouds.append(hour["clouds"])
                if dt.hour >= 23 and dt.day == nextDay:
                    break

        return clouds
