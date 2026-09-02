from unittest.mock import Mock, call
from src.core.scheduler import Scheduler
from src.protocols.time_manager_protocol import TimeManagerProtocol
from src.utils.schedule_entry import ScheduleEntry
from pathlib import Path
import pytest

## SET TIME MANAGER TESTS
def test_set_time_manager_sets_correctly():
    #Arrange
    scheduler = Scheduler()
    time_manager = Mock(spec=TimeManagerProtocol)

    #Act
    scheduler.set_time_manager(time_manager=time_manager)

    #Assert
    assert scheduler._time_manager == time_manager

def test_set_time_manager_does_nothing_when_argument_is_none():
    #Arrange
    scheduler = Scheduler()
    scheduler._time_manager = Mock()

    #Act
    scheduler.set_time_manager(time_manager=None)

    #Assert
    assert scheduler._time_manager != None

def test_set_time_manager_does_not_override_existing_time_manager():
    #Arrange
    scheduler = Scheduler()
    scheduler._time_manager = Mock()
    time_manager = Mock(spec=TimeManagerProtocol)
    #Act
    scheduler.set_time_manager(time_manager=time_manager)

    #Assert
    assert scheduler._time_manager != time_manager

## GET IRRIGATION TIME TESTS
def test_get_irrigation_time_returns_default_time_when_time_not_specified():
    #Arrange
    scheduler = Scheduler()
    

    #Act
    returned_value = scheduler.get_irrigation_time("section1")

    #Assert
    assert returned_value == scheduler._default_irrigation_time

@pytest.mark.parametrize("key,value",{"seciton1":15,"section3":1,"section5":30,"section10":50}.items(),)
def test_get_irrigation_time_returns_specified_time(key,value):
    #Arrange
    scheduler = Scheduler()
    scheduler._specific_section_irrigation_time = {key:value}

    #Act
    returned_value = scheduler.get_irrigation_time(key)

    #Assert
    assert returned_value == scheduler._specific_section_irrigation_time[key]

@pytest.mark.parametrize("adjustment",[0.7,-0.2,-0.5,1,0,-1,0.5])
def test_get_irrigation_time_correclty_calculates_adjustment(adjustment):
    #Arrange
    scheduler = Scheduler()
    scheduler._adjustment = adjustment

    #Act
    returned_value = scheduler.get_irrigation_time("section1")

    #Assert
    assert returned_value == scheduler._default_irrigation_time*(1+scheduler._adjustment)


## GET SCHEDULE FOR DAY
@pytest.mark.parametrize("day,expected",[
    ("Monday",ScheduleEntry(start_time="06:00",sections=["section1","section2"])),
    ("Tuesday",ScheduleEntry(start_time="08:00",sections=["section3","section5"])),
    ("Friday",ScheduleEntry(start_time="03:00",sections=["all"])),
    ("Lolday",ScheduleEntry(start_time=None,sections=[])),
    ])
def test_get_schedule_for_day_returns_correct_schedule(day,expected):
    #Arrange
    scheduler = Scheduler()
    scheduler._time_manager = Mock(spec=TimeManagerProtocol)
    scheduler._time_manager.current_month = "February"
    scheduler._schedule = {"Monday":ScheduleEntry(start_time="06:00",sections=["section1","section2"]),
                           "Tuesday":ScheduleEntry(start_time="08:00",sections=["section3","section5"]),
                           "Friday":ScheduleEntry(start_time="03:00",sections=["all"])}
    #Act
    schedule = scheduler.get_schedule_for_day(day)

    #Assert
    assert schedule == expected

def test_get_schedule_for_day_returns_empty_schedule_during_winter():
    #Arrange
    scheduler = Scheduler()
    scheduler._time_manager = Mock(spec=TimeManagerProtocol)
    scheduler._winter_months = ["February"]
    scheduler._time_manager.current_month = "February"

    #Act
    returned_value = scheduler.get_schedule_for_day("Monday")

    #Assert
    assert returned_value == ScheduleEntry(start_time=None,sections=[])

## SET CALLBACK ON SCHEDULE CHANGE TESTS
def test_set_callback_on_schedule_change_sets_callback_correctly():
    #Arrange
    scheduler = Scheduler()
    callback1 = Mock(__name__="callback1")

    #Act
    scheduler.set_callback_on_schedule_change(callback1)

    #Assert
    assert scheduler._callbacks_on_schedule_change.__contains__(callback1)

def test_set_callback_does_not_add_non_callable():
    #Arrange
    scheduler = Scheduler()
    non_callable = 1

    #Act
    scheduler.set_callback_on_schedule_change(non_callable)

    #Assert
    assert len(scheduler._callbacks_on_schedule_change) == 0

## LOAD X FROM JSON FILE
@pytest.mark.parametrize("loader_function",["load_schedule_from_json_file","load_irrigation_times_from_json_file","load_winter_months_from_json_file","load_weather_adjustment_from_json_file"])
def test_load_x_from_json_file_does_nothing_when_input_is_not_file(loader_function):
    #Arrange
    import copy
    scheduler = Scheduler()
    scheduler_snapshot = copy.deepcopy(scheduler)
    json_file = Path("tmp")
    loader = getattr(scheduler,loader_function)
    #Act
    loader(json_file)
    
    #Assert
    assert scheduler._schedule == scheduler_snapshot._schedule
    assert scheduler._winter_months == scheduler_snapshot._winter_months
    assert scheduler._adjustment == scheduler_snapshot._adjustment
    assert scheduler._specific_section_irrigation_time == scheduler_snapshot._specific_section_irrigation_time
    assert scheduler._default_irrigation_time == scheduler_snapshot._default_irrigation_time

@pytest.mark.parametrize("loader_function",["load_schedule_from_json_file","load_irrigation_times_from_json_file","load_winter_months_from_json_file","load_weather_adjustment_from_json_file"])
def test_load_x_from_json_file_does_nothing_when_json_decode_error_occurs(tmp_path,loader_function):
    #Arrange
    import json
    import copy
    scheduler = Scheduler()
    scheduler_snapshot = copy.deepcopy(scheduler)
    json_file = tmp_path/"shedule.json"
    json_file.write_text(" ")
    loader = getattr(scheduler,loader_function)
    #Act
    loader(json_file)

    #Assert
    assert scheduler._schedule == scheduler_snapshot._schedule
    assert scheduler._winter_months == scheduler_snapshot._winter_months
    assert scheduler._adjustment == scheduler_snapshot._adjustment
    assert scheduler._specific_section_irrigation_time == scheduler_snapshot._specific_section_irrigation_time
    assert scheduler._default_irrigation_time == scheduler_snapshot._default_irrigation_time

## LOAD SCHEDULE FROM JSON FILE TESTS
def test_load_schedule_from_json_file_loads_schedule_config(tmp_path):
    #Arrange
    import json
    scheduler = Scheduler()
    json_file = tmp_path/"shedule.json"
    json_file.write_text('{"Monday":{"start_time":"04:00","sections":["all"]}}',encoding="utf-8")

    #Act
    scheduler.load_schedule_from_json_file(json_file)

    #Assert
    assert scheduler._schedule["Monday"] == ScheduleEntry(start_time="04:00",sections=["all"])

def test_load_schedule_from_json_file_does_not_change_schedule_when_fields_do_not_exist(tmp_path):
    #Arrange
    import json
    scheduler = Scheduler()
    json_file = tmp_path/"shedule.json"
    json_file.write_text('{"Monday":{}}',encoding="utf-8")

    #Act
    scheduler.load_schedule_from_json_file(json_file)

    #Assert
    assert scheduler._schedule["Monday"] == ScheduleEntry(start_time="04:00",sections=["all"])

def test_load_shedule_from_json_sets_multiple_entries(tmp_path):
    #Arrange
    import json
    scheduler = Scheduler()
    json_file = tmp_path/"shedule.json"
    json_file.write_text('{"Monday":{"start_time":"04:00","sections":["all"]},' \
    '"Tuesday":{"start_time":"04:00","sections":["all"]},' \
    '"Wednesday":{"start_time":"04:00","sections":[]},' \
    '"Thursday":{"start_time":"04:00","sections":["all"]}}')

    #Act
    scheduler.load_schedule_from_json_file(json_file)

    #Assert
    assert scheduler._schedule == { "Monday":ScheduleEntry(start_time="04:00",sections=["all"]),
                                    "Tuesday":ScheduleEntry(start_time="04:00",sections=["all"]),
                                    "Wednesday":ScheduleEntry(start_time="04:00",sections=[]),
                                    "Thursday":ScheduleEntry(start_time="04:00",sections=["all"]),
                                    "Friday": ScheduleEntry(start_time=None, sections=[]),
                                    "Saturday": ScheduleEntry(start_time='04:00', sections=['all']),
                                    "Sunday": ScheduleEntry(start_time=None, sections=[])
                                    }

## LOAD IRRIGATION TIMES FROM JSON TESTS
def test_load_irrigation_times_from_json_file_changes_deafault_irrigation_time(tmp_path):
    #Arrange
    import json
    scheduler = Scheduler()
    json_file = tmp_path/"irrigation_times.json"
    json_file.write_text('{"default":20}')

    #Act
    scheduler.load_irrigation_times_from_json_file(json_file)

    #Assert
    assert scheduler._default_irrigation_time == 20

def test_load_irrigation_times_from_json_file_changes_specific_irrigation_time(tmp_path):
    #Arrange
    import json
    scheduler = Scheduler()
    json_file = tmp_path/"irrigation_times.json"
    json_file.write_text('{"section1":20}')

    #Act
    scheduler.load_irrigation_times_from_json_file(json_file)

    #Assert
    assert scheduler._specific_section_irrigation_time["section1"] == 20

def test_load_irrigation_times_from_json_file_does_nothing_when_string_as_value(tmp_path):
    #Arrange
    import json
    import copy
    scheduler = Scheduler()
    scheduler._default_irrigation_time = 15
    json_file = tmp_path/"irrigation_times.json"
    json_file.write_text('{"default":"bad_input"}')

    #Act
    scheduler.load_irrigation_times_from_json_file(json_file)

    #Assert
    assert scheduler._default_irrigation_time == 15

def test_load_irrigation_times_from_json_file_does_nothing_when_number_as_string_value(tmp_path):
    #Arrange
    import json
    import copy
    scheduler = Scheduler()
    scheduler._default_irrigation_time = 15
    json_file = tmp_path/"irrigation_times.json"
    json_file.write_text('{"default":"50"}')

    #Act
    scheduler.load_irrigation_times_from_json_file(json_file)

    #Assert
    assert scheduler._default_irrigation_time == 15

## LOAD WINTER MONTHS FROM JSON FILE TESTS
def test_load_winter_months_from_json_file_sets_months(tmp_path):
    #Arrange
    import json
    scheduler = Scheduler()
    json_file = tmp_path/"winter_moths.json"
    json_file.write_text('["January","February"]')

    #Act
    scheduler.load_winter_months_from_json_file(json_file)

    #Assert
    assert scheduler._winter_months == ["January","February"]

def test_load_winter_months_from_json_file_does_nothing_when_invalid_data_typ_in_array(tmp_path):
    #Arrange
    import json
    scheduler = Scheduler()
    json_file = tmp_path/"winter_moths.json"
    json_file.write_text('["January","February",123]')

    #Act
    scheduler.load_winter_months_from_json_file(json_file)

    #Assert
    assert scheduler._winter_months == []

def test_load_winter_months_from_json_file_does_nothing_when_input_is_not_array(tmp_path):
    #Arrange
    import json
    scheduler = Scheduler()
    json_file = tmp_path/"winter_moths.json"
    json_file.write_text('{"January":"Monday"}')

    #Act
    scheduler.load_winter_months_from_json_file(json_file)

    #Assert
    assert scheduler._winter_months == []

def test_load_winter_months_from_json_file_does_nothing_when_input_is_array_of_dicts(tmp_path):
    #Arrange
    import json
    scheduler = Scheduler()
    json_file = tmp_path/"winter_moths.json"
    json_file.write_text('[{"January":"Monday"},{"February":"Wednesday"},{"March":123}]')

    #Act
    scheduler.load_winter_months_from_json_file(json_file)

    #Assert
    assert scheduler._winter_months == []

def test_load_winter_months_from_json_file_does_nothing_when_input_is_array_of_arrays(tmp_path):
    #Arrange
    import json
    scheduler = Scheduler()
    json_file = tmp_path/"winter_moths.json"
    json_file.write_text('[[],[],[]]')

    #Act
    scheduler.load_winter_months_from_json_file(json_file)

    #Assert
    assert scheduler._winter_months == []

## LOAD WEATHER ADJUSTMENT FORM JSON FILE
def test_load_weather_adjustment_from_json_file_loads_adjustment(tmp_path):
    #Arrange
    import json
    scheduler = Scheduler()
    json_file = tmp_path/"weather_adjustment.json"
    json_file.write_text('{"adj_percentage": 25, "total_pop": 0.5, "days_analyzed": 5, "avg_max_temps": 26.43, "max_temp": 28.95}')

    #Act
    scheduler.load_weather_adjustment_from_json_file(json_file)

    #Assert
    assert scheduler._adjustment == round(25/100,2)

def test_load_weather_adjustment_from_json_file_does_nothing_when_input_is_not_a_dict(tmp_path):
    #Arrange
    import json
    scheduler = Scheduler()
    json_file = tmp_path/"weather_adjustment.json"
    json_file.write_text('[{"adj_percentage": 25, "total_pop": 0.5, "days_analyzed": 5, "avg_max_temps": 26.43, "max_temp": 28.95}]')
    scheduler._adjustment = 10
    #Act
    scheduler.load_weather_adjustment_from_json_file(json_file)

    #Assert
    assert scheduler._adjustment == 10