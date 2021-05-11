# Optimise Charge of Home Battery Maximising Use Of Solar Energy

The aim of the project is to optimise the charging of a home energy store (battery) to maximise the use of solar energy generation. Where the forecast does not predict enough will be generated the fall back configures a control system to pre-charge the battery with the minimum amount of cheap rate electricity needed before solar takes over.

## Objectives

The main objectives

- To assist the planet by making making the most of renewable energy, where as much as possible is from home generation
- To reduce the cost of household energy bills

# Architecture

The project was built for the following home configuration but the concepts and much of the code are developed with portability to other home configurations in mind

- 4kwh solar generation through a Fronius inverter
- 8.2kw GivEnergy lipo battery and inverter
- Immersun to divert excess energy to heat water using the immersion element in the hot water cylinder.
  - This works independantly of the control system and only diverts excess to the hot water cylinder when the battery is charged and there is excess capacity the house is not using
- Octopus Go tarriff to provide cheap rate (economy 7) electricity during the night
- Synology NAS that runs 24 by 7.
  - The control logic to optimise the battery charge is to set to run automatically several times a day

## Solution

The solution uses the following data :-

- The weather forecast for the next day to predict how much energy can be generated from the solar system for every daylight hour
- Take into account varying daylight hours across the year
- Expected eenergy use of the home for each hour of the day
- Max charge solar can deliver to the battery per hour
- Capacity of the battery
- Min level the battery should be charged to
- Time period for cheap rate electricity

This data is used to determine how much the battery needs to be pre-charged using cheap rate (economy 7) electricity between 00:30 and 04:30. On an hour by hour basis it looks at

- The energy needs of the house
- How much energy is generated each hour

Resulting in

- A percentage that the battery needs to be pre-charged
- A prediction of how much "excess" energy will be generated and available

The program then updates the GivEnergy control system to:-

- Run _Mode 1 Dynamic_ make the most of solar generation
- Run _Battery Smart Charge_ Mode
- Set the start and end time to pre-charge the battery
- Set the percentage to pre-charge the battery

# Implementaiton

The solution is

- Written in python
- Runs in a docker container on a Synology NAS
  - It runs a few times in the hours leading up to the start of the cheap rate electricity with a view to using the most upto date weather forecast
  - For testing it runs from in VS Code and from a python command line on windows
- Calls [openweathermap](https://openweathermap.org/api) to get the weather forecast for each hour of the next day.
  - To determine how much energy the solar panels will generate the cloud cover for each hour is used
- Uses [Selenium](https://www.selenium.dev/) a screen scraping technology to access the GivEnergy cloud control panel
  - Programmatically navigates the web interface as though it was a human and sets the control parameters
  - **Note** screen scraping was used as no API was available at the time. GivEnergy are working to provide an API which will dramatically simplifiy the program once available.
- Uses [keyrings.cryptfile](https://pypi.org/project/keyrings.cryptfile/) to access credntials needed to access the GivEnergy cloud.
- Uses python logging module for all output which is also used for debugging.

## Configuration

All parameters are stored in a configuration file _battery.conf_ an example can be seen below

```
[economy7]
starttime=0035
endtime=0430

[battery]
mincharge=30
solarhourlycharge=2
gridhourlycharge=2.5
maxcharge=7.0
houseuse=0.2,0.2,0.2,0.2,0.2,0.2,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,1.5,1.5,0.4,0.4,0.4,0.4

[daylight]
fromsummer=08
tosummer=18
fromwinter=09
towinter=16

[givcloud]
system=giv
id=loginID

```

# Run

The program is executed as a pythod program :-

```
battery.py -d <configdir>
```

where <configdir> is the directory that contains the confugration file battey.conf

## Log output

Below is an example of the log output from the program

```
2021-05-11 19:45:34,767 - battery.determinePreCharge - INFO - hour 0 cloudcvr 29 use -0.20 precharge -0.20 gen 0.00 high 0.00
2021-05-11 19:45:34,768 - battery.determinePreCharge - INFO - hour 1 cloudcvr 36 use -0.40 precharge -0.40 gen 0.00 high 0.00
2021-05-11 19:45:34,768 - battery.determinePreCharge - INFO - hour 2 cloudcvr 35 use -0.60 precharge -0.60 gen 0.00 high 0.00
2021-05-11 19:45:34,768 - battery.determinePreCharge - INFO - hour 3 cloudcvr 27 use -0.80 precharge -0.80 gen 0.00 high 0.00
2021-05-11 19:45:34,769 - battery.determinePreCharge - INFO - hour 4 cloudcvr 24 use -1.00 precharge -1.00 gen 0.00 high 0.00
2021-05-11 19:45:34,769 - battery.determinePreCharge - INFO - hour 5 cloudcvr 19 use -1.20 precharge -1.20 gen 0.00 high 0.00
2021-05-11 19:45:34,769 - battery.determinePreCharge - INFO - hour 6 cloudcvr 16 use -1.60 precharge -1.60 gen 0.00 high 0.00
2021-05-11 19:45:34,770 - battery.determinePreCharge - INFO - hour 7 cloudcvr 13 use -2.00 precharge -2.00 gen 0.00 high 0.00
2021-05-11 19:45:34,771 - battery.determinePreCharge - INFO - hour 8 cloudcvr 1 use -0.42 precharge -2.00 gen 1.98 high 0.00
2021-05-11 19:45:34,771 - battery.determinePreCharge - INFO - hour 9 cloudcvr 5 use 1.08 precharge -2.00 gen 1.90 high 1.08
2021-05-11 19:45:34,772 - battery.determinePreCharge - INFO - hour 10 cloudcvr 10 use 2.48 precharge -2.00 gen 1.80 high 2.48
2021-05-11 19:45:34,773 - battery.determinePreCharge - INFO - hour 11 cloudcvr 19 use 3.70 precharge -2.00 gen 1.62 high 3.70
2021-05-11 19:45:34,774 - battery.determinePreCharge - INFO - hour 12 cloudcvr 31 use 4.68 precharge -2.00 gen 1.38 high 4.68
2021-05-11 19:59:21,336 - battery.determinePreCharge - INFO - hour 13 cloudcvr 42 use 5.44 precharge -2.00 gen 1.16 high 5.44
2021-05-11 19:45:34,774 - battery.determinePreCharge - INFO - hour 14 cloudcvr 98 spare 0.00 gen 0.04
2021-05-11 19:45:34,775 - battery.determinePreCharge - INFO - hour 15 cloudcvr 99 spare 0.00 gen 0.02
2021-05-11 19:45:34,775 - battery.determinePreCharge - INFO - hour 16 cloudcvr 99 spare 0.00 gen 0.02
2021-05-11 19:45:34,776 - battery.determinePreCharge - INFO - hour 17 cloudcvr 99 spare 0.00 gen 0.02
2021-05-11 19:45:34,777 - battery.determinePreCharge - INFO - hour 18 cloudcvr 100 spare 0.00 gen 0.00
2021-05-11 19:45:34,777 - battery.determinePreCharge - INFO - hour 19 cloudcvr 100 spare 0.00 gen 0.00
2021-05-11 19:45:34,778 - battery.determinePreCharge - INFO - hour 20 cloudcvr 100 spare 0.00 gen 0.00
2021-05-11 19:45:34,779 - battery.determinePreCharge - INFO - hour 21 cloudcvr 100 spare 0.00 gen 0.00
2021-05-11 19:45:34,779 - battery.determinePreCharge - INFO - hour 22 cloudcvr 100 spare 0.00 gen 0.00
2021-05-11 19:45:34,780 - battery.determinePreCharge - INFO - hour 23 cloudcvr 100 spare 0.00 gen 0.00
2021-05-11 19:45:34,781 - battery.determinePreCharge - INFO - Tomorrow set min battery charge to 29
2021-05-11 19:45:34,781 - battery.determinePreCharge - INFO - Tomorrow additional spare capacity 0kWh
2021-05-11 19:45:34,782 - givAutomate.setChromeDriverLocal - INFO - using local chrome web driver
2021-05-11 19:45:35,925 - givAutomate.configBatteryCharge - INFO - Set Giv to charge between 0035 & 0135 charging to 29%
2021-05-11 19:45:37,021 - givAutomate.configBatteryCharge - INFO - using account id xxxxx
2021-05-11 19:45:37,027 - givAutomate.configBatteryCharge - INFO - At web page Login page - GivEnergy Cloud
2021-05-11 19:45:37,272 - givAutomate.configBatteryCharge - INFO - Press Login
2021-05-11 19:45:43,365 - givAutomate.configBatteryCharge - INFO - At web page xxxxx - GivEnergy Cloud
2021-05-11 19:45:48,971 - givAutomate.configBatteryCharge - INFO - At web page Monitor information - GivEnergy Cloud
2021-05-11 19:45:49,312 - givAutomate.configBatteryCharge - INFO - Smart charge selected? True
2021-05-11 19:45:54,426 - givAutomate.configBatteryCharge - INFO - Successfully set Giv to charge between 0035 & 0135 charging to 29%
2021-05-11 19:45:54,427 - givAutomate.configBatteryCharge - INFO - close webdriver
```

# Todo

Following are a list of future items to be worked given some spare time

- Rework to use GivEnergy API rather than screen scrape the web interface
- Setup HomeAssistant and create a dashboard related to control program and its output
