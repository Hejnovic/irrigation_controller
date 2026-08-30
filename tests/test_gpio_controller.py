from unittest.mock import Mock, call

from src.core.gpio_controller import GPIOController
from src.utils.schedule_entry import ScheduleEntry
import pytest
PIN_CONFIG = { "pump": 17, "section1":27, "section2":22 }
## START IRRIGATION AUTO TESTS
def test_start_irrigation_auto_does_nothing_when_schedule_empty():
    #Arrange
    controller = GPIOController(PIN_CONFIG)
    controller.set_value = Mock()
    controller._switch_to_next_section = Mock()
    controller._daily_schedule = Mock(sections=[])

    #Act
    controller.start_irrigation_auto()

    #Assert
    controller.set_value.assert_not_called()
    controller._switch_to_next_section.assert_not_called()

def test_start_irrigation_auto_does_nothing_when_schedule_is_none():
    #Arrange
    controller = GPIOController(PIN_CONFIG)
    controller.set_value = Mock()
    controller._switch_to_next_section = Mock()
    controller._daily_schedule = Mock(sections=None)

    #Act
    controller.start_irrigation_auto()

    #Assert
    controller.set_value.assert_not_called()
    controller._switch_to_next_section.assert_not_called()
    
def test_start_irrigation_auto_does_correctly_fetch_sections_when_schedule_is_all():
    #Arrange
    controller = GPIOController(PIN_CONFIG)
    controller.set_value = Mock()
    controller._switch_to_next_section = Mock()
    controller._daily_schedule = Mock(sections=["all"])

    #Act
    controller.start_irrigation_auto()
    

    #Assert
    assert controller._sections_to_irrigate == sorted(controller._pin_mapping.keys() - {"pump"})
    controller.set_value.assert_called_once_with("pump",False)
    controller._switch_to_next_section.assert_called_once()

def test_start_irrigation_auto_switches_to_next_section_when_schedule_not_empty():
    #Arrange
    controller = GPIOController(PIN_CONFIG)
    controller._scheduler = Mock()
    controller._time_manager = Mock()
    controller._dashboard_updater = Mock()
    controller.set_value = Mock()
    controller._daily_schedule = Mock(sections=["section1", "section2", "section3"])


    #Act
    controller.start_irrigation_auto()
    assert controller._sections_to_irrigate == ["section2", "section3"]
    assert controller._current_section == controller._daily_schedule.sections[0]
    controller._time_end = None

    controller._switch_to_next_section()
    assert controller._sections_to_irrigate == ["section3"]
    assert controller._current_section == controller._daily_schedule.sections[1]
    controller._time_end = None

    controller._switch_to_next_section()
    assert controller._sections_to_irrigate == []
    assert controller._current_section == controller._daily_schedule.sections[2]
    controller._time_end = None

    controller.stop_device = Mock()
    controller._switch_to_next_section()

    #Assert
    controller.stop_device.assert_called_once()
    controller.set_value.assert_has_calls([ 
        call("pump", False),
        call("section1",False),
        call("section2",False),
        call("section3",False),
    ])

## CHECK IF SHOULD SWITCH SECTION TESTS
def test_check_if_should_switch_section_triggers_when_time_reached_and_device_is_irrigating():
    #Arrange
    controller = GPIOController(PIN_CONFIG)
    controller._time_manager = Mock()
    controller._scheduler = Mock()
    controller._dashboard_updater = Mock()
    controller.set_value = Mock()
    controller._irrigation_state = controller.IrrigationState.IRRIGATING
    controller._switch_to_next_section = Mock()
    controller._time_end = "11:50"
    controller._time_manager.current_hour_minute = "11:50"


    #Act
    controller.check_if_should_switch_section("it doesn't even matter")

    #Assert
    controller.set_value.assert_called_once()
    controller._switch_to_next_section.assert_called_once()

def test_check_if_should_switch_section_triggers_when_time_is_not_reached_and_device_is_irrigating():
    #Arrange
    controller = GPIOController(PIN_CONFIG)
    controller._time_manager = Mock()
    controller._scheduler = Mock()
    controller._dashboard_updater = Mock()
    controller.set_value = Mock()
    controller._irrigation_state = controller.IrrigationState.IRRIGATING
    controller._switch_to_next_section = Mock()
    controller._time_end = "11:50"
    controller._time_manager.current_hour_minute = "11:40"

    #Act
    controller.check_if_should_switch_section("it doesn't even matter")

    #Assert
    controller.set_value.assert_not_called()
    controller._switch_to_next_section.assert_not_called()

def test_check_if_should_switch_section_does_not_trigger_when_device_is_idle():
    #Arrange
    controller = GPIOController(PIN_CONFIG)
    controller._time_manager = Mock()
    controller._scheduler = Mock()
    controller._dashboard_updater = Mock()
    controller.set_value = Mock()
    controller._irrigation_state = controller.IrrigationState.IDLE
    controller._switch_to_next_section = Mock()

    #Act
    controller.check_if_should_switch_section("it doesn't even matter")

    #Assert
    controller.set_value.assert_not_called()
    controller._switch_to_next_section.assert_not_called()

def test_check_if_should_switch_section_does_not_trigger_when_device_is_idle_with_fake_data_that_allows_switching():
    #Arrange
    controller = GPIOController(PIN_CONFIG)
    controller._time_manager = Mock()
    controller._scheduler = Mock()
    controller._dashboard_updater = Mock()
    controller.set_value = Mock()
    controller._irrigation_state = controller.IrrigationState.IDLE
    controller._current_section = "section1"  # weird state
    controller._time_end = "11:50"
    controller._time_manager.current_hour_minute = "11:50"
    controller._switch_to_next_section = Mock()

    #Act
    controller.check_if_should_switch_section("it doesn't even matter")

    #Assert
    controller.set_value.assert_not_called()
    controller._switch_to_next_section.assert_not_called()

## SET VALUE TESTS
def test_set_value_turns_on_pin():
    #Arrange
    from gpiod.line import Value
    controller = GPIOController(PIN_CONFIG)
    controller._gpio.reset_mock()
    

    #Act
    controller.set_value("pump", True)

    #Assert
    controller._gpio.set_value.assert_called_once_with(17, Value.ACTIVE)

def test_set_value_turns_off_pin():
    #Arrange
    from gpiod.line import Value
    controller = GPIOController(PIN_CONFIG)
    controller._gpio.reset_mock()

    #Act
    controller.set_value("section1", False)

    #Assert
    controller._gpio.set_value.assert_called_once_with(27, Value.INACTIVE)

def test_set_value_does_not_act_for_invalid_pin():
    #Arrange
    controller = GPIOController(PIN_CONFIG)
    controller._gpio.reset_mock()

    #Act
    controller.set_value("section3",False)

    #Assert
    controller._gpio.set_value.assert_not_called()

## START SELECTED SECTION TESTS
def test_start_selected_section_does_nothing_when_state_is_irrigating():
    #Arrange
    controller = GPIOController(PIN_CONFIG)
    controller._gpio.reset_mock()
    controller.set_value = Mock()
    controller.stop_device = Mock()

    controller._irrigation_state = controller.IrrigationState.IRRIGATING
    #Act

    controller.start_selected_section()

    #Assert
    controller.set_value.assert_not_called()
    controller.stop_device.assert_not_called()

def test_start_selected_section_does_nothing_when_state_is_manual_pump():
    #Arrange
    controller = GPIOController(PIN_CONFIG)
    controller._gpio.reset_mock()
    controller.set_value = Mock()
    controller.stop_device = Mock()

    controller._irrigation_state = controller.IrrigationState.MANUAL_PUMP
    #Act

    controller.start_selected_section()

    #Assert
    controller.set_value.assert_not_called()
    controller.stop_device.assert_not_called()
    assert controller._irrigation_state == controller.IrrigationState.MANUAL_PUMP

def test_start_selected_section_stops_device_when_state_is_already_manual_section():
    #Arrange
    controller = GPIOController(PIN_CONFIG)
    controller._gpio.reset_mock()
    controller.set_value = Mock()
    controller.stop_device = Mock()

    controller._irrigation_state = controller.IrrigationState.MANUAL_SECTION
    #Act

    controller.start_selected_section()

    #Assert
    controller.set_value.assert_not_called()
    controller.stop_device.assert_called_once()
    assert controller._irrigation_state == controller.IrrigationState.IDLE

def test_start_selected_section_defaults_to_section1_when_chosen_section_is_none():
    #Arrange
    controller = GPIOController(PIN_CONFIG)
    controller._gpio.reset_mock()
    controller._dashboard_updater = Mock()
    controller.set_value = Mock()
    controller.stop_device = Mock()
    controller._chosen_section = None
    controller._irrigation_state = controller.IrrigationState.IDLE
    #Act

    controller.start_selected_section()

    #Assert
    assert controller._chosen_section == "section1"
    controller.set_value.assert_has_calls([call("pump",False),call("section1",False)],any_order=True)
    controller._dashboard_updater.update_active_section.assert_called_once()
    assert controller._irrigation_state == controller.IrrigationState.MANUAL_SECTION
    controller.stop_device.assert_not_called()

def test_start_selected_section_defaults_to_section1_when_chosen_section_is_empty_array():
    #Arrange
    controller = GPIOController(PIN_CONFIG)
    controller._gpio.reset_mock()
    controller._dashboard_updater = Mock()
    controller.set_value = Mock()
    controller.stop_device = Mock()
    controller._chosen_section = []
    controller._irrigation_state = controller.IrrigationState.IDLE
    #Act

    controller.start_selected_section()

    #Assert
    assert controller._chosen_section == "section1"
    controller.set_value.assert_has_calls([call("pump",False),call("section1",False)],any_order=True)
    controller._dashboard_updater.update_active_section.assert_called_once()
    assert controller._irrigation_state == controller.IrrigationState.MANUAL_SECTION
    controller.stop_device.assert_not_called()

def test_start_selected_section_defaults_to_section1_when_chosen_section_is_empty():
    #Arrange
    controller = GPIOController(PIN_CONFIG)
    controller._gpio.reset_mock()
    controller._dashboard_updater = Mock()
    controller.set_value = Mock()
    controller.stop_device = Mock()
    controller._chosen_section
    controller._irrigation_state = controller.IrrigationState.IDLE
    #Act

    controller.start_selected_section()

    #Assert
    assert controller._chosen_section == "section1"
    controller.set_value.assert_has_calls([call("pump",False),call("section1",False)],any_order=True)
    controller._dashboard_updater.update_active_section.assert_called_once()
    assert controller._irrigation_state == controller.IrrigationState.MANUAL_SECTION
    controller.stop_device.assert_not_called()

def test_start_selected_section_runs_chosen_section():
    #Arrange
    controller = GPIOController(PIN_CONFIG)
    controller._gpio.reset_mock()
    controller._dashboard_updater = Mock()
    controller.set_value = Mock()
    controller.stop_device = Mock()
    controller._chosen_section = "section3"
    controller._irrigation_state = controller.IrrigationState.IDLE
    #Act

    controller.start_selected_section()

    #Assert
    assert controller._chosen_section == "section3"
    controller.set_value.assert_has_calls([call("pump",False),call("section3",False)],any_order=True)
    controller._dashboard_updater.update_active_section.assert_called_once()
    assert controller._irrigation_state == controller.IrrigationState.MANUAL_SECTION
    controller.stop_device.assert_not_called()

## CHOSE SECTION TESTS

def test_chose_section_does_nothing_when_section_out_of_range():   
    #Arrange 
    controller = GPIOController(PIN_CONFIG)
    controller._chosen_section = "section3"
    controller._irrigation_state = controller.IrrigationState.IDLE
    #Act

    controller.choose_section(6)

    #Assert
    assert controller._chosen_section == "section3"

def test_chose_section_changes_section_to_selected():   
    #Arrange 
    controller = GPIOController(PIN_CONFIG)
    controller._chosen_section = "section3"
    controller._irrigation_state = controller.IrrigationState.IDLE
    #Act

    controller.choose_section(2)

    #Assert
    assert controller._chosen_section == "section2"

## RUN PUMP TESTS

def test_run_pump_starts_when_irrigation_state_is_idle():   
    #Arrange 
    controller = GPIOController(PIN_CONFIG)
    controller._gpio.reset_mock()
    controller._dashboard_updater = Mock()
    controller.set_value = Mock()
    controller._irrigation_state = controller.IrrigationState.IDLE
    #Act

    controller.run_pump(1)

    #Assert
    controller.set_value.assert_called_once_with("pump",False)
    assert controller._irrigation_state == controller.IrrigationState.MANUAL_PUMP

def test_run_pump_stops_when_irrigation_state_is_manual_pump():   
    #Arrange 
    controller = GPIOController(PIN_CONFIG)
    controller._gpio.reset_mock()
    controller._dashboard_updater = Mock()
    controller.set_value = Mock()
    controller._irrigation_state = controller.IrrigationState.MANUAL_PUMP
    #Act

    controller.run_pump(0)

    #Assert
    controller.set_value.assert_called_once_with("pump",True)
    assert controller._irrigation_state == controller.IrrigationState.IDLE

def test_run_pump_does_nothing_when_irrigation_state_is_manual_pump_and_called_with_1():   
    #Arrange 
    controller = GPIOController(PIN_CONFIG)
    controller._gpio.reset_mock()
    controller._dashboard_updater = Mock()
    controller.set_value = Mock()
    controller._irrigation_state = controller.IrrigationState.MANUAL_PUMP
    #Act

    controller.run_pump(1)

    #Assert
    controller.set_value.assert_not_called()
    assert controller._irrigation_state == controller.IrrigationState.MANUAL_PUMP

def test_run_pump_does_nothing_when_irrigation_state_is_idle_and_called_with_0():   
    #Arrange 
    controller = GPIOController(PIN_CONFIG)
    controller._gpio.reset_mock()
    controller._dashboard_updater = Mock()
    controller.set_value = Mock()
    controller._irrigation_state = controller.IrrigationState.IDLE
    #Act

    controller.run_pump(0)

    #Assert
    controller.set_value.assert_not_called()
    assert controller._irrigation_state == controller.IrrigationState.IDLE

def test_run_pump_does_not_interrupt_auto_irrigation():
    #Arrange 
    controller = GPIOController(PIN_CONFIG)
    controller._gpio.reset_mock()
    controller._dashboard_updater = Mock()
    controller.set_value = Mock()
    controller._irrigation_state = controller.IrrigationState.IRRIGATING
    #Act

    controller.run_pump(0)

    #Assert
    controller.set_value.assert_not_called()
    assert controller._irrigation_state == controller.IrrigationState.IRRIGATING

## CHECK IF SHOULD START IRRIGATION TESTS

def test_check_if_should_start_irrigation_runs_when_device_is_idle_and_all_requirments_are_met():
    #Arrange
    controller = GPIOController(PIN_CONFIG)
    controller._gpio.reset_mock()
    controller._time_manager = Mock()
    controller._dashboard_updater = Mock()
    controller.start_irrigation_auto = Mock()
    controller._daily_schedule = Mock(sections=["section1", "section2", "section3"],start_time="12:00")
    controller._irrigation_state = controller.IrrigationState.IDLE
    controller._time_manager.current_hour_minute = "12:00"
    #Act
    controller.check_if_should_start_irrigation("it doesn't even matter")

    #Assert
    controller.start_irrigation_auto.assert_called_once()
    assert controller._irrigation_state == controller.IrrigationState.IRRIGATING

@pytest.mark.parametrize("state",["IRRIGATING","MANUAL_PUMP","MANUAL_SECTION"])
def test_check_if_should_start_irrigation_does_nothing_when_device_is_not_in_idle_state(state):
    #Arrange
    controller = GPIOController(PIN_CONFIG)
    controller._gpio.reset_mock()
    controller._time_manager = Mock()
    controller._dashboard_updater = Mock()
    controller.start_irrigation_auto = Mock()
    controller._daily_schedule = Mock(sections=["section1", "section2", "section3"],start_time="12:00")
    controller._time_manager.current_hour_minute = "12:00"
    controller._irrigation_state = getattr(controller.IrrigationState,state)


    #Act
    controller.check_if_should_start_irrigation("it doesn't even matter")


    #Assert
    controller.start_irrigation_auto.assert_not_called()
    assert controller._irrigation_state == getattr(controller.IrrigationState,state)

def test_check_if_should_start_irrigation_does_nothing_when_current_time_is_different_than_start_time():
    #Arrange
    controller = GPIOController(PIN_CONFIG)
    controller._gpio.reset_mock()
    controller._time_manager = Mock()
    controller._dashboard_updater = Mock()
    controller.start_irrigation_auto = Mock()
    controller._daily_schedule = Mock(sections=["section1", "section2", "section3"],start_time="12:00")
    controller._time_manager.current_hour_minute = "13:00"
    controller._irrigation_state = controller.IrrigationState.IDLE


    #Act
    controller.check_if_should_start_irrigation("it doesn't even matter")


    #Assert
    controller.start_irrigation_auto.assert_not_called()
    assert controller._irrigation_state == controller.IrrigationState.IDLE

def test_check_if_should_start_irrigation_does_nothing_when_schedule_is_empty():
    #Arrange
    controller = GPIOController(PIN_CONFIG)
    controller._gpio.reset_mock()
    controller._time_manager = Mock()
    controller._dashboard_updater = Mock()
    controller.start_irrigation_auto = Mock()
    controller._daily_schedule = Mock(sections=[],start_time="12:00")
    controller._time_manager.current_hour_minute = "12:00"
    controller._irrigation_state = controller.IrrigationState.IDLE

    #Act
    controller.check_if_should_start_irrigation("it doesn't even matter")

    #Assert
    controller.start_irrigation_auto.assert_not_called()
    assert controller._irrigation_state == controller.IrrigationState.IDLE

def test_check_if_should_start_irrigation_does_nothing_when_start_time_is_empty():
    #Arrange
    controller = GPIOController(PIN_CONFIG)
    controller._gpio.reset_mock()
    controller._time_manager = Mock()
    controller._dashboard_updater = Mock()
    controller.start_irrigation_auto = Mock()
    controller._daily_schedule = Mock(sections=["section1", "section2", "section3"],start_time="")
    controller._time_manager.current_hour_minute = "12:00"
    controller._irrigation_state = controller.IrrigationState.IDLE

    #Act
    controller.check_if_should_start_irrigation("it doesn't even matter")

    #Assert
    controller.start_irrigation_auto.assert_not_called()
    assert controller._irrigation_state == controller.IrrigationState.IDLE

## SET DAILY SCHEDULE TESTS
@pytest.mark.parametrize("day",["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])
def test_set_daily_schedule_sets_daily_schedule_correctly(day):
    #Arrange
    schedule: dict[str, ScheduleEntry] = { #Default schedule, can be loaded from config file
        "Monday": ScheduleEntry(start_time="04:00", sections=["all"]),
        "Tuesday": ScheduleEntry(start_time="04:00", sections=["section3"]),
        "Wednesday": ScheduleEntry(start_time="04:00", sections=["all"]),
        "Thursday": ScheduleEntry(start_time="04:00", sections=["section3"]),
        "Friday": ScheduleEntry(start_time=None, sections=[]),
        "Saturday": ScheduleEntry(start_time="04:00", sections=["all"]),
        "Sunday": ScheduleEntry(start_time=None, sections=[])
    }
    controller = GPIOController(PIN_CONFIG)
    controller._gpio.reset_mock()   
    controller._scheduler = Mock()
    controller._daily_schedule = None
    controller._scheduler.get_schedule_for_day.return_value = schedule[day]

    #Act
    controller.set_daily_schedule(day)

    #Assert
    controller._scheduler.get_schedule_for_day.assert_called_once_with(day)
    assert controller._daily_schedule == schedule[day]
    assert isinstance(controller._daily_schedule, ScheduleEntry)

def test_set_daily_schedule_does_not_set_none_as_schedule():
    #Arrange
    controller = GPIOController(PIN_CONFIG)
    controller._gpio.reset_mock()   
    controller._scheduler = Mock()
    controller._daily_schedule = None
    controller._scheduler.get_schedule_for_day.return_value = None

    #Act
    controller.set_daily_schedule("Monday")

    #Assert
    controller._scheduler.get_schedule_for_day.assert_called_once_with("Monday")
    assert isinstance(controller._daily_schedule, ScheduleEntry)
    assert controller._daily_schedule == ScheduleEntry(start_time=None,sections=[])

