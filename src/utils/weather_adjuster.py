"""
CRON JOB FOR IRRIGATION CONTROLLER THAT FETCHES WEATHER DATA FROM OPENWEATHER AND THEN DOES CALCULATIONS ON HOW TO ADJUST NEXT IRRIGATION

"""

from time_manager import TimeManager
from pathlib import Path
from dotenv import load_dotenv
import requests
import os
import json

env_path = Path("/opt/src/irrigationcontrol/configs/env/weather_adjuster.env") #Hardcoded for now, wonder if cron job can be supplied env like systemd service

if os.path.exists(env_path):
   load_dotenv(env_path)


API_KEY = os.getenv["OPENWEATHER_API_KEY"]
LAT = float(os.getenv["LAT"])
LON = float(os.getenv["LON"])
BREAKPOINT_TEMP = int(os.getenv["BREAKPOINT_TEMP"]) #IN CELCIUS
ADJ_PER_DEGREE = int(os.getenv["ADJ_PER_DEGREE"]) #IN PERCENTAGE POINT
RAIN_WEIGHT = int(os.getenv["RAIN_WEIGHT"]) #PARAM THAT MAKES RAIN MORE OR LESS SIGNIFICANT IN CALCULATIONS, THE NUMBER PUT HERE IS MAXIMUM NEGATIVE IT WILL REACH
MIN_ADJ = int(os.getenv["MIN_ADJ"])
MAX_ADJ = int(os.getenv["MAX_ADJ"])
UNITS = os.getenv["UNITS"] #For example metric
TARGET_FILE = Path(os.getenv["TARGET_FILE"]) #In my case the file is in irrigation configs folder and watchdog has added callbacks if the file changes
#ASSERTING ALL ENV EXIST

#OPENWEATHER_API_CALL
r = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={API_KEY}&units={UNITS}")

if r.status_code == 200:
   data = r.json()
   daily_max = {}
   for reading in data["list"]:
       dt_txt = reading.get("dt_txt", "")[:10] #10 chars from 2026-09-24 12:00:00 leaves only 2026-09-24 
       temp_max = reading["main"].get("temp_max") or reading["main"].get("temp",0)
       if dt_txt not in daily_max:
          daily_max[dt_txt] = temp_max
       else:
          daily_max[dt_txt] = max(daily_max[dt_txt], temp_max)

#ASSERTING MAX TEMPS IS NOT EMPTY
max_temps = daily_max.values()

avg_max_temp = sum(max_temps)/len(max_temps)
highest_temp = max(max_temps) #Biggest from all days

#ADJUSTMENT IN PERCENTAGE
#HEAT ADJUSTMENT
adjustment = 0
if avg_max_temp > BREAKPOINT_TEMP:
    adjustment += (avg_max_temp-BREAKPOINT_TEMP)*ADJ_PER_DEGREE
#BONUS FOR 20% AND 40% ABOVE BREAKPOINT_TEMP
if highest_temp >= 1.2*BREAKPOINT_TEMP:
   adjustment += ADJ_PER_DEGREE
if highest_temp >= 1.4*BREAKPOINT_TEMP:
   adjustment += 2*ADJ_PER_DEGREE

#RAIN ADJUSTMENT
total_pop = sum(reading.get("pop", 0) for reading in data["list"]) / len(data["list"])
#PROBABILITY FOR RAIN (POP IS BETWEEN 0 AND 1)
adjustment -= total_pop*RAIN_WEIGHT

#MAKES THE ADJUSTMENT ALWAYS BE BETWEEN SUPPLIED MIN AND MAX 
adjustment = max(MIN_ADJ, min(adjustment, MAX_ADJ))

print(f"Adjustment Percentage: {adjustment}, avg_max_temp: {avg_max_temp}, highest_temp: {highest_temp}, days_analyzed {len(max_temps)}, avg_pop: {total_pop}")
tmp_path = TARGET_FILE.with_suffix('.tmp')
data ={"adj_percentage":adjustment,"avg_max_temp": avg_max_temp,"highest_temp":highest_temp,"days_analyzed": len(max_temps),"rain_chance": total_pop}
try:
    with open(tmp_path, 'w', encoding='utf-8') as f:
         json.dump(data, f, indent=2, ensure_ascii=False)
         tmp_path.replace(TARGET_FILE)
except Exception as e:
    if tmp_path.exists():
        tmp_path.unlink()