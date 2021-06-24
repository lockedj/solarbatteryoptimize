from automateDJL import weather
import platform
import logging
import logging.config
import configparser
from datetime import datetime
import os
import sys
import getopt
import math
from datetime import time, timedelta, datetime, date
import http.client
import json

# todo - update NAS to run daily
# todo - web site to show output
# todo - run chrome in headless mode


class Battery:
    # Determine how much to charge battery at cheap rate based
    # how much sun there is likely to be the next day.
    # Must run this the day before to set the giv controller config
    # prior to cheap rate energy period

    def __init__(self, dir, file):
        self.configdir = dir
        self.configfile = file
        self.loadConfig()
        return

    def loadConfig(self):
        try:
            config = configparser.ConfigParser()
            config.read(self.configdir+self.configfile)
            self.cloudfromsummer = config.getint(
                "daylight", "fromsummer", fallback=8)
            self.cloudtosummer = config.getint(
                "daylight", "tosummer", fallback=18)
            self.cloudfromwinter = config.getint(
                "daylight", "fromwinter", fallback=9)
            self.cloudtowinter = config.getint(
                "daylight", "towinter", fallback=16)
            self.preCharge = config.getint("battery", "mincharge", fallback=30)
            self.hourlycharge = config.getint(
                "battery", "solarhourlycharge", fallback=2)
            self.gridhourlycharge = config.getfloat(
                "battery", "gridhourlycharge", fallback=2.5)
            self.maxcharge = config.getfloat(
                "battery", "maxcharge", fallback=7.0)
            self.houseuse = config.get(
                "battery", "houseuse").split(",")
            self.cheapRateFrom = config.get(
                "economy7", "starttime", fallback="0030")
            self.cheapRateTo = config.get(
                "economy7", "endtime", fallback="0430")
            self.givsystem = config.get("givcloud", "system")
            self.givid = config.get("givcloud", "id")
            self.apitoken = config.get("givcloud", "apitoken")
            # self.givpwd = config.get("givcloud", "pwd")
        except:
            logging.getLogger().exception(
                "Problem reading battery config file"+self.configdir+"battery.conf")
        return

    def determineEndTime(self, precharge):
        # Work out end time to stop pre-charging the battery - no need to use more
        # from the grid than needed
        chargekwh = (precharge/100) * self.maxcharge
        timerequired = chargekwh / self.gridhourlycharge
        addhours = math.floor(timerequired)
        remaintime = timerequired-addhours
        addmins = 0
        if remaintime >= 0 and remaintime < .25:
            addmins = 15
        elif remaintime >= .25 and remaintime < .50:
            addmins = 30
        elif remaintime >= .50 and remaintime < .75:
            addmins = 45
        else:
            addhours = addhours+1

        starttime = time(
            hour=int(self.cheapRateFrom[0:2]), minute=int(self.cheapRateFrom[2:4]))
        startdate = datetime.combine(date.today(), starttime)
        td = timedelta(seconds=(addhours*60*60)+(addmins*60))
        enddate = startdate+td
        endtime = enddate.strftime('%H%M')
        return endtime

    def determinePreCharge(self):
        now = datetime.today()
        month = now.month
        if month >= 4 and month < 10:
            cloudfrom = self.cloudfromsummer
            cloudto = self.cloudtosummer
        else:
            cloudfrom = self.cloudfromwinter
            cloudto = self.cloudtowinter

        forecast = weather.Weather()
        clouds = forecast.cloudTomorrow()

        hr = 0          # hour of the day being processed
        use = 0         # house use + battery charge
        gen = 0         # how much generated in selected hour
        highcharge = 0  # Highest kWh battery will get to
        charge = 0      # Min kWh to pre-charge the battery

        # First calculate if there is enough forecast solar radiation to both cover
        # basic house use and to charge the battery. The result of the calculation is
        # the min the battery neds to be charged from the grid to ensure the house
        # does not need to use the grid outside of cheaprate/economy 7 electriciy (either
        # through solar generated electriciy of use of the battery)
        # Note: there are times when this is not possible on days when there is not much
        # sun and the battery is not big enough to cover the house use
        while hr < 24:
            use = use - float(self.houseuse[hr])    # Subtract house use
            gen = 0                                 # default gnerated is 0
            if hr >= cloudfrom and hr <= cloudto:   # If daylight hour
                if clouds[hr] < 100:
                    gen = self.hourlycharge*((100-clouds[hr])/100)
                    # no daylight so no gen
            use = use + gen                         # total of house use + generated

            if use < charge:                        # If demand is greater than current precharge
                charge = use                        # set pre-charge to demand
            if use > highcharge:                    # Remember high use
                highcharge = use

            logging.getLogger().info(
                f"hour {hr} cloudcvr {clouds[hr]} use {use:0.2f} precharge {charge:0.2f} gen {gen:0.2f} high {highcharge:0.2f}")

            if -charge > self.maxcharge:            # If precharge needed is more than
                # set precharge to max capacity
                charge = -int(self.maxcharge)
                hr = hr+1
                break                               # needs max charge
            if (highcharge - charge) >= self.maxcharge:  # If gen more than capacity then
                hr = hr+1
                break                               # stop as precharge known
            hr = hr+1

        # calculate additional solar capacity over and above what is needed
        # by the battery. This can then be used for other devices like the dishwasher..
        spare = 0       # additional solar capacity over and above needs of battery
        while hr < 24:
            gen = 0
            use = use - float(self.houseuse[hr])    # Subtract house use
            if hr >= cloudfrom and hr <= cloudto:   # If daylight houg
                if clouds[hr] < 100:
                    gen = self.hourlycharge*((100-clouds[hr])/100)
                    houseuse = float(self.houseuse[hr])
                    if gen > houseuse:
                        spare = spare + gen - houseuse   # add in generation
            logging.getLogger().info(
                f"hour {hr} cloudcvr {clouds[hr]} spare {spare:0.2f} gen {gen:0.2f}")
            hr = hr+1

        charge = -charge

        chargePercent = int(round((charge/self.maxcharge)*100))
        logging.getLogger().info(
            "Tomorrow set min battery charge to {}%".format(chargePercent))
        logging.getLogger().info(
            f"Tomorrow additional spare capacity {spare:0.2f}kWh")

        return chargePercent

    def configBatteryCharge(self, cheapRateFrom, chargeToTime, charge):
        conn = http.client.HTTPSConnection("api.givenergy.cloud")

        payload = json.dumps({
            "enable": True,
            "start": cheapRateFrom,
            "finish": chargeToTime,
            "chargeToPercent": charge
        })
        headers = {
            'Authorization': self.apitoken,
            'Content-Type': 'application/json'
        }
        conn.request("POST", "/chargeBattery", payload, headers)
        res = conn.getresponse()
        if res.status == 200:
            data = res.read()
            result = data.decode("utf-8")
            logging.getLogger().info(f"HTTP response {result}")
            jsonres = json.loads(result)
            # if result == "Changes Set":
            if jsonres["chargeFlag"] == "1":
                logging.getLogger().info(
                    f"Successfully set Giv to charge between {cheapRateFrom} & {chargeToTime} charging to {charge}%")
            else:
                logging.getLogger().error("Failed to set charge: {}".format(result))
        else:
            logging.getLogger().error(
                f"HTTP request to charge battery failed: {res.status} {res.reason}")
        return


def main(argv):
    configdir = ''
    configfile = "dlbattery.conf"
#   configfile = "battery.conf"

    try:
        opts, args = getopt.getopt(argv, "hd:f:", ["cdir="])
    except getopt.GetoptError:
        print('battery.py -d <configdir> -c <configfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('battery.py -d <configdir> -c <configfile>')
            sys.exit()
        elif opt in ("-d", "--cdir"):
            configdir = arg + "/"
        elif opt in ("-c", "--cfile"):
            configfile = arg

    logging.config.fileConfig(fname=configdir+'logging.conf',
                              disable_existing_loggers=False)
    # Get the logger specified in the file
    logger = logging.getLogger("automateDJL")
    logger.debug("Start configure solar battery economy 7 charge ")

    try:
        battery = Battery(configdir, configfile)
        charge = battery.determinePreCharge()
        chargeToTime = battery.determineEndTime(charge)
        # Update the giv control system with charge times and volumes
        battery.configBatteryCharge(battery.cheapRateFrom,
                                    chargeToTime, charge)

        # Update the giv control system with charge volume.  If on dev machine use local web driver,
        # if on NAS then need to use remote web driver to access the docker
        # container running selenium
        # NOTE the old screen scraping approach is no longer needed as there is
        # an API now available to read and configured the battery control system
        #giv = givAutomate.GivAutomate(configdir)
        # if platform.system() == "Windows":
        #    giv.setChromeDriverLocal()
        # else:
        #    giv.setChromeDriverRemote()
        # giv.configBatteryCharge(battery.cheapRateFrom,
        #                        chargeToTime, charge)

    except:
        logger.exception("giv update failed")
        raise
    finally:
        logger.debug("End configure solar battery economy 7 charge ")


if __name__ == "__main__":
    main(sys.argv[1:])
