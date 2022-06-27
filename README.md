# Optimise Charge of Home Battery Maximising Use Of Solar Energy

The aim of the project is to optimise the charging of a home energy store (battery) to maximise the use of solar energy generation. Where the forecast does not predict enough will be generated the fall back configures a battery control system to pre-charge the battery with the minimum amount of cheap rate electricity needed before solar takes over.

## Objectives

The main objectives

- To assist the planet by making making the most of renewable energy, where as much as possible is from home generation
- To reduce the cost of household energy bills

# Architecture

The project was built for the following home configuration but the concepts and much of the code are developed with portability to other home configurations in mind

- 4kwh solar generation through a Fronius inverter
- 8.2kw GivEnergy lipo battery and inverter (a 2nd 8.2kw battery has been added)
- Immersun to divert excess energy to heat water using the immersion element in the hot water cylinder.
  - This works independantly of the control system and only diverts excess to the hot water cylinder when the battery is charged and there is excess capacity the house is not using
- Octopus Go faster tarriff to provide cheap rate (economy 7) electricity during the night.
- Synology NAS that runs 24 by 7.
  - The control logic to optimise the battery charge is to set to run automatically several times a day

## Solution

The solution uses the following data :-

- The weather forecast for the next day to predict how much energy can be generated from the solar system for every daylight hour
- Take into account varying daylight hours across the year
- Expected energy use of the home for each hour of the day
- Max charge solar can deliver to the battery per hour
- Capacity of the battery
- Min level the battery should be charged to
- Time period for cheap rate electricity

This data is used to determine how much the battery needs to be pre-charged using cheap rate (economy 7) electricity in octopus go faster cheap rate hours (00:30 and 04:30). On an hour by hour basis it looks at

- The energy needs of the house
- How much energy is expected to be generated each hour of the next day

Resulting in

- A percentage that the battery needs to be pre-charged
- A prediction of how much "excess" energy will be generated and available
- The period the battery should pull cheap rate energy from the grid

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
  - For testing it runs in VS Code and from a python command line on windows
- Calls [openweathermap](https://openweathermap.org/api) to get the weather forecast for each hour of the next day.
  - To determine how much energy the solar panels will generate the cloud cover for each hour is used
- Claculatge the required amount the battery needs to be charged to based on predicated cloud cover.
- Uses python http and the GivEnergy V1 API to update the inverter to charge the battery to the calculated amount
- Uses python logging module for all output which is also used for debugging.

## Configuration

All parameters are stored in a configuration file _battery.conf_ an example can be seen below.

- Copy the conf file and customise to meet your requirements
- For waather forecast a free account can be created at https://openweathermap.org/ and
  from there an API Key can be generated
- An API Token needs to be generated on the giv cloud portal settings page

```
[economy7]
starttime=00:35           // Cheap rate electricity starts at
endtime=04:30             // Cheap rate electricity ends at

[battery]
mincharge=30              // Min to be charged to during cheap rate
solarhourlycharge=2       // Max PV charge per hour assuming no clouds
gridhourlycharge=2.5      // Charge per hour from the grid
maxcharge=7.0             // Battery capacity or max to charge to
houseuse=0.2,0.2,0.2,0.2,0.2,0.2,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,1.5,1.5,0.4,0.4,0.4,0.4
                          // House energy profile by hour starting at minight in kwh
[daylight]
fromsummer=08             // Start hour PV is generated from in summer
tosummer=18               // Hour when PV stops in summer
fromwinter=09             // Start hour PV is generated from in winter
towinter=16               // Hour when PV gen stops in winter

[givcloud]
system=giv
id=<giv loginID>          // giv login ID
apitoken=<givcloud API token from Giv web portal>

[weather]
openweatherapitoken=<api token from open weather api>

[location]
gpslat=your latitude
gpslong=your longigtude
```

# Run

The program is executed as a python program :-

```
python battery.py -d <configdir> -d <configfile>
```

where <configdir> is the directory that contains the confugration file
and <configfile> is the name of the config file

It should be scheduled to run prior to the start of the cheap rate electricity period. A  
good approach is to schedule it to run at least once a day automatically on a device that
runs 24/7, something like a NAS or Raspberry PI... Once set up it can be left to run 365 days
a year, then sit back and watch the savings build up.

## Log output

Below is an example of the log output from the program

```
C:\Python39\python.exe' 'c:\Users\locke\.vscode\extensions\ms-python.python-2022.4.1\pythonFiles\lib\python\debugpy\launcher' '63385' '--' 'c:\Users\locke\Documents\Projects\HomeSolar\battery.py'
2022-04-27 11:07:52,405 - battery.determinePreCharge - INFO - hour 0 cloudcvr 87 use -0.30 precharge -0.30 gen 0.00 high 0.00
2022-04-27 11:07:52,405 - battery.determinePreCharge - INFO - hour 1 cloudcvr 89 use -0.60 precharge -0.60 gen 0.00 high 0.00
2022-04-27 11:07:52,405 - battery.determinePreCharge - INFO - hour 2 cloudcvr 15 use -0.90 precharge -0.90 gen 0.00 high 0.00
2022-04-27 11:07:52,406 - battery.determinePreCharge - INFO - hour 3 cloudcvr 12 use -1.20 precharge -1.20 gen 0.00 high 0.00
2022-04-27 11:07:52,406 - battery.determinePreCharge - INFO - hour 4 cloudcvr 12 use -1.50 precharge -1.50 gen 0.00 high 0.00
2022-04-27 11:07:52,406 - battery.determinePreCharge - INFO - hour 5 cloudcvr 20 use -1.80 precharge -1.80 gen 0.00 high 0.00
2022-04-27 11:07:52,407 - battery.determinePreCharge - INFO - hour 6 cloudcvr 22 use -2.20 precharge -2.20 gen 0.00 high 0.00
2022-04-27 11:07:52,407 - battery.determinePreCharge - INFO - hour 7 cloudcvr 28 use -3.10 precharge -3.10 gen 0.00 high 0.00
2022-04-27 11:07:52,407 - battery.determinePreCharge - INFO - hour 8 cloudcvr 88 use -3.76 precharge -3.76 gen 0.24 high 0.00
2022-04-27 11:07:52,407 - battery.determinePreCharge - INFO - hour 9 cloudcvr 90 use -3.96 precharge -3.96 gen 0.20 high 0.00
2022-04-27 11:07:52,407 - battery.determinePreCharge - INFO - hour 10 cloudcvr 80 use -3.96 precharge -3.96 gen 0.40 high 0.00
2022-04-27 11:07:52,408 - battery.determinePreCharge - INFO - hour 11 cloudcvr 83 use -4.02 precharge -4.02 gen 0.34 high 0.00
2022-04-27 11:07:52,408 - battery.determinePreCharge - INFO - hour 12 cloudcvr 87 use -4.16 precharge -4.16 gen 0.26 high 0.00
2022-04-27 11:07:52,408 - battery.determinePreCharge - INFO - hour 13 cloudcvr 88 use -4.32 precharge -4.32 gen 0.24 high 0.00
2022-04-27 11:07:52,408 - battery.determinePreCharge - INFO - hour 14 cloudcvr 100 use -4.72 precharge -4.72 gen 0.00 high 0.00
2022-04-27 11:07:52,408 - battery.determinePreCharge - INFO - hour 15 cloudcvr 100 use -5.12 precharge -5.12 gen 0.00 high 0.00
2022-04-27 11:07:52,408 - battery.determinePreCharge - INFO - hour 16 cloudcvr 100 use -5.52 precharge -5.52 gen 0.00 high 0.00
2022-04-27 11:07:52,409 - battery.determinePreCharge - INFO - hour 17 cloudcvr 100 use -5.92 precharge -5.92 gen 0.00 high 0.00
2022-04-27 11:07:52,409 - battery.determinePreCharge - INFO - hour 18 cloudcvr 100 use -7.92 precharge -7.92 gen 0.00 high 0.00
2022-04-27 11:07:52,409 - battery.determinePreCharge - INFO - hour 19 cloudcvr 100 use -9.42 precharge -9.42 gen 0.00 high 0.00
2022-04-27 11:07:52,410 - battery.determinePreCharge - INFO - hour 20 cloudcvr 100 use -10.22 precharge -10.22 gen 0.00 high 0.00
2022-04-27 11:07:52,410 - battery.determinePreCharge - INFO - hour 21 cloudcvr 100 use -11.02 precharge -11.02 gen 0.00 high 0.00
2022-04-27 11:07:52,411 - battery.determinePreCharge - INFO - hour 22 cloudcvr 100 use -11.52 precharge -11.52 gen 0.00 high 0.00
2022-04-27 11:07:52,411 - battery.determinePreCharge - INFO - hour 23 cloudcvr 100 use -11.92 precharge -11.92 gen 0.00 high 0.00
2022-04-27 11:07:52,412 - battery.determinePreCharge - INFO - Tomorrow set min battery charge to 79%
2022-04-27 11:07:52,412 - battery.determinePreCharge - INFO - Tomorrow additional spare capacity 0.00kWh
2022-04-27 11:07:56,311 - battery.configBatteryCharge - INFO - HTTP response {"data":{"success":true,"message":"Written Successfully"}}
2022-04-27 11:07:56,312 - battery.configBatteryCharge - INFO - Successfully set Giv to charge between 23:30 & 02:30 charging to 79%

```

# Todo

Following are a list of future items to be worked given some spare time

- Experiment with solcast solar forecast. (Not in any rush as the openweathermap api and hourly cloud forecast as given good results)

# History

- 12/05/21 Prior to May 21 the program used [Selenium](https://www.selenium.dev/) a screen scraping technology to access the GivEnergy cloud control panel. Selenium was used to programmatically navigate the web interface as though it was a human and to set the control parameters. With the advent of the giv cloud beta API this technique is no longer required and the program has been greatly simplified by using the API.
- 27/04/22 Updated to use the GivEnergy V1 API along with some small tweaks and tidyig up.
- 20/06/22 When GiVTCP runs it keeps the inverter busy which means calls to the cloud api can fail with inverter busy. Added retry logic around the cloud api call.
- 27/06/22 Parametised house location and open weather maps api key. Updated the readme.
