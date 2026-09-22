import pytest
from src.utils.dashboard_updater import DashboardUpdater
from src.utils.enums import IrrigationState
from unittest.mock import Mock, call
from src.utils.schedule_entry import ScheduleEntry
from src.utils.enums import MQTTTopics
## UPDATE DATETIME TESTS
def test_update_datetime_calls_publish_with_correct_data():
    #Arrange
    dashboard_updater = DashboardUpdater()
    dashboard_updater._mqtt_manager = Mock()
    dashboard_updater._time_manager = Mock()
    dashboard_updater._time_manager.current_datetime = "04:00"
    dashboard_updater._time_manager.current_day_of_week = "Monday"

    #Act
    dashboard_updater.update_datetime("does not matter")

    #Assert
    dashboard_updater._mqtt_manager.publish.assert_called_with("ds/deviceTime",f"04:00 - Monday",qos=MQTTTopics.DEVICE_TIME.qos,retain=True)

## UPDATE ACTIVE SECTION TESTS (might rename to update dashboard)
def test_update_ative_section_idle_state():
    #Arrange
    dashboard_updater = DashboardUpdater()
    dashboard_updater._mqtt_manager = Mock()
    dashboard_updater._time_manager = Mock()
    dashboard_updater._translator = Mock()
    dashboard_updater._translator.translate.return_value = "XXX"
    state = IrrigationState.IDLE

    #Act
    dashboard_updater.update_active_section(state)

    #Assert
    dashboard_updater._translator.translate.assert_called_once_with("device_idle")
    dashboard_updater._mqtt_manager.publish.assert_called_with("ds/activeSection","XXX",qos=MQTTTopics.ACTIVE_SECTION.qos,retain=True)

def test_update_ative_section_irrigating_state():
    #Arrange
    dashboard_updater = DashboardUpdater()
    dashboard_updater._mqtt_manager = Mock()
    dashboard_updater._time_manager = Mock()
    dashboard_updater._translator = Mock()
    dashboard_updater._translator.translate.return_value = "XXX"
    dashboard_updater.update_time_interval = Mock()
    state = IrrigationState.IRRIGATING

    #Act
    dashboard_updater.update_active_section(state,section="section1",time_interval=15,time_end="15:50",)

    #Assert
    dashboard_updater._mqtt_manager.publish.assert_called_once_with("ds/activeSection","XXX",qos=MQTTTopics.ACTIVE_SECTION.qos,retain=True)
    dashboard_updater._translator.translate.assert_called_once_with("section_running_auto",section="1")
    dashboard_updater.update_time_interval.assert_called_once_with(time_interval=15,time_end="15:50")

def test_update_ative_section_manual_pump_state():
    #Arrange
    dashboard_updater = DashboardUpdater()
    dashboard_updater._mqtt_manager = Mock()
    dashboard_updater._time_manager = Mock()
    dashboard_updater._translator = Mock()
    dashboard_updater._translator.translate.return_value = "XXX"
    state = IrrigationState.MANUAL_PUMP

    #Act
    dashboard_updater.update_active_section(state)

    #Assert
    dashboard_updater._translator.translate.assert_called_once_with("pump_running_manual")
    dashboard_updater._mqtt_manager.publish.assert_called_once_with("ds/activeSection","XXX",qos=MQTTTopics.ACTIVE_SECTION.qos,retain=True)

def test_update_ative_section_manual_section_state():
    #Arrange
    dashboard_updater = DashboardUpdater()
    dashboard_updater._mqtt_manager = Mock()
    dashboard_updater._time_manager = Mock()
    dashboard_updater._translator = Mock()
    dashboard_updater._translator.translate.return_value = "XXX"
    state = IrrigationState.MANUAL_SECTION

    #Act
    dashboard_updater.update_active_section(state,section="section1")

    #Assert
    dashboard_updater._translator.translate.assert_called_once_with("section_running_manual",section="1")
    dashboard_updater._mqtt_manager.publish.assert_called_once_with("ds/activeSection","XXX",qos=MQTTTopics.ACTIVE_SECTION.qos,retain=True)

def test_update_ative_section_error_state():
    #Arrange
    dashboard_updater = DashboardUpdater()
    dashboard_updater._mqtt_manager = Mock()
    dashboard_updater._time_manager = Mock()
    dashboard_updater._translator = Mock()
    dashboard_updater._translator.translate.return_value = "XXX"
    state = IrrigationState.ERROR

    #Act
    dashboard_updater.update_active_section(state,section="section1")

    #Assert
    dashboard_updater._translator.translate.assert_called_once_with("error")
    dashboard_updater._mqtt_manager.publish.assert_called_once_with("ds/activeSection","XXX",qos=MQTTTopics.ACTIVE_SECTION.qos,retain=True)

## UPDATE TIME INTERVAL TESTS
def test_update_time_interval_calls_publish_with_data():
    #Arrange
    dashboard_updater = DashboardUpdater()
    dashboard_updater._mqtt_manager = Mock()
    dashboard_updater._time_manager = Mock()
    dashboard_updater._translator = Mock()
    dashboard_updater._translator.translate.return_value = "XXX"

    #Act
    dashboard_updater.update_time_interval(time_end="16:30",time_interval=50)

    #Assert
    dashboard_updater._translator.translate.assert_called_once_with("time_interval_auto",time_end="16:30",time_interval=50)
    dashboard_updater._mqtt_manager.publish.assert_called_once_with("ds/timeInterval","XXX",qos=MQTTTopics.TIME_INTERVAL.qos,retain=True)

def test_update_time_interval_calls_publish_with_data():
    #Arrange
    dashboard_updater = DashboardUpdater()
    dashboard_updater._mqtt_manager = Mock()
    dashboard_updater._time_manager = Mock()
    dashboard_updater._translator = Mock()
    dashboard_updater._translator.translate.return_value = "XXX"

    #Act
    dashboard_updater.update_time_interval(time_interval="16:20")

    #Assert
    dashboard_updater._translator.translate.assert_not_called()
    dashboard_updater._mqtt_manager.publish.assert_called_with("ds/timeInterval","",qos=MQTTTopics.TIME_INTERVAL.qos,retain=True)

## UPDATE SCHEDULE TESTS
def test_update_schedule_with_sections_all():
    #Arrange
    dashboard_updater = DashboardUpdater()
    dashboard_updater._mqtt_manager = Mock()
    dashboard_updater._time_manager = Mock()
    dashboard_updater._translator = Mock()
    dashboard_updater._translator.translate.return_value = "XXX"

    #Act
    dashboard_updater.update_schedule(ScheduleEntry(start_time="04:00",sections=["all"]))

    #Assert
    dashboard_updater._mqtt_manager.publish.assert_called_with("ds/currentSchedule","XXX",qos=MQTTTopics.CURRENT_SCHEDULE.qos,retain=True)

def test_update_schedule_with_sections_empty():
    #Arrange
    dashboard_updater = DashboardUpdater()
    dashboard_updater._mqtt_manager = Mock()
    dashboard_updater._time_manager = Mock()
    dashboard_updater._translator = Mock()
    dashboard_updater._translator.translate.return_value = "XXX"

    #Act
    dashboard_updater.update_schedule(ScheduleEntry(start_time=None,sections=[]))

    #Assert
    dashboard_updater._mqtt_manager.publish.assert_called_with("ds/currentSchedule","XXX",qos=MQTTTopics.CURRENT_SCHEDULE.qos,retain=True)

def test_update_schedule_with_specified_sections():
    #Arrange
    dashboard_updater = DashboardUpdater()
    dashboard_updater._mqtt_manager = Mock()
    dashboard_updater._time_manager = Mock()
    dashboard_updater._translator = Mock()
    dashboard_updater._translator.translate.return_value = "XXX"

    #Act
    dashboard_updater.update_schedule(ScheduleEntry(start_time="04:00",sections=["section2","section1","section5"]))

    #Assert
    dashboard_updater._mqtt_manager.publish.assert_called_with("ds/currentSchedule","XXX",qos=MQTTTopics.CURRENT_SCHEDULE.qos,retain=True)

## RESET DASHBOARD BUTTONS TESTS
def test_reset_dashboard_buttons_calls_publish():
    #Arrange
    dashboard_updater = DashboardUpdater()
    dashboard_updater._mqtt_manager = Mock()
    dashboard_updater._time_manager = Mock()
    dashboard_updater._translator = Mock()
    dashboard_updater._translator.translate.return_value = "XXX"

    #Act
    dashboard_updater.reset_dashboard_buttons()

    #Assert
    dashboard_updater._mqtt_manager.publish.assert_has_calls([call("ds/startSection",0,qos=MQTTTopics.START_SECTION.qos),call("ds/runPump",0,qos=MQTTTopics.RUN_PUMP.qos)])

def test_reset_dashbord_button_calls_publish():
    #Arrange
    dashboard_updater = DashboardUpdater()
    dashboard_updater._mqtt_manager = Mock()
    dashboard_updater._time_manager = Mock()
    dashboard_updater._translator = Mock()
    dashboard_updater._translator.translate.return_value = "XXX"

    #Act
    dashboard_updater.reset_dashboard_button(MQTTTopics.RUN_PUMP.downlink)

    #Assert
    dashboard_updater._mqtt_manager.publish.assert_called_with("downlink/ds/runPump", 0)