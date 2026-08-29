from unittest.mock import Mock, call

from src.core.gpio_controller import GPIOController

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

##START SELECTED SECTION TESTS

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
    controller.set_value.assert_not_called
    controller.stop_device.assert_not_called

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
    controller.set_value.assert_not_called
    controller.stop_device.assert_not_called
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
    controller.set_value.assert_not_called
    controller.stop_device.assert_called_once
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
    controller._dashboard_updater.assert_called_once
    assert controller._irrigation_state == controller.IrrigationState.MANUAL_SECTION
    controller.stop_device.assert_not_called

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
    controller._dashboard_updater.assert_called_once
    assert controller._irrigation_state == controller.IrrigationState.MANUAL_SECTION
    controller.stop_device.assert_not_called

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
    controller._dashboard_updater.assert_called_once
    assert controller._irrigation_state == controller.IrrigationState.MANUAL_SECTION
    controller.stop_device.assert_not_called

def test_start_selected_section_runs_chosen_section():
    #Arrange
    controller = GPIOController(PIN_CONFIG)
    controller._gpio.reset_mock()
    controller._dashboard_updater = Mock()
    controller.set_value = Mock()
    controller.stop_device = Mock()
    controller._chosen_section = "section3"
    controller._irrigation_state == controller.IrrigationState.IDLE
    #Act

    controller.start_selected_section()

    #Assert
    assert controller._chosen_section == "section3"
    controller.set_value.assert_has_calls([call("pump",False),call("section3",False)],any_order=True)
    controller._dashboard_updater.assert_called_once
    assert controller._irrigation_state == controller.IrrigationState.MANUAL_SECTION
    controller.stop_device.assert_not_called
