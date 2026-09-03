from unittest.mock import Mock, call, AsyncMock, patch
from pathlib import Path
import pytest
from src.utils.watchdog import ConfigWatcher
import asyncio
from watchfiles import Change
## INNIT TEST
def test_innit_gather_all_config_files(tmp_path):
    #Arrange
    json_file_1 = tmp_path/"json_file_1.json"
    json_file_1.write_text('{}')

    #Act
    watchdog = ConfigWatcher(tmp_path)

    #Assert
    assert len(watchdog._config_files) == 1

## REGISTER HANDLER TESTS
def test_register_handler_adds_callback_to_config_file(tmp_path):
    #Arrange
    json_file_1 = tmp_path/"json_file_1.json"
    json_file_1.write_text('{}')
    watchdog = ConfigWatcher(tmp_path)
    callback = Mock(__name__ = "callback")

    #Act
    watchdog.register_handler("json_file_1.json",callback)

    #Assert
    watchdog._handlers[json_file_1] == callback

def test_register_handler_does_nothing_when_file_does_not_exist(tmp_path):
    #Arrange
    json_file_1 = tmp_path/"json_file_1.json"
    json_file_1.write_text('{}')
    watchdog = ConfigWatcher(tmp_path)
    callback = Mock(__name__ = "callback")

    #Act
    watchdog.register_handler("json_file_2.json",callback)

    #Assert
    assert len(watchdog._handlers) == 0

## START TESTS
@pytest.mark.asyncio
async def test_start_preloads_existing_configs(tmp_path):
    #Arrange
    json_file_1 = tmp_path/"json_file_1.json"
    json_file_1.write_text('{}')
    watchdog = ConfigWatcher(tmp_path)
    watchdog._watch = AsyncMock()
    callback = Mock(__name__ = "callback")
    watchdog.register_handler("json_file_1.json",callback)


    #Act
    with patch('src.utils.watchdog.awatch'):
        await watchdog.start()

    #Assert
    callback.assert_called_with(tmp_path/"json_file_1.json")

@pytest.mark.asyncio
async def test_start_calls_watch(tmp_path):
    #Arrange
    watchdog = ConfigWatcher(tmp_path)
    watchdog._watch = AsyncMock()


    #Act
    with patch('src.utils.watchdog.awatch'):
        await watchdog.start()

    #Assert
    watchdog._watch.assert_called_once()

## WATCH TESTS
@pytest.mark.parametrize("event,expected",[("modified","assert_called_once"),("added","assert_called_once"),("deleted","assert_not_called"),])
@pytest.mark.asyncio
async def test_watch(tmp_path,event,expected):
    #Arrange
    json_file_1 = tmp_path/"json_file_1.json"
    json_file_1.write_text('{}')
    watchdog = ConfigWatcher(tmp_path)
    callback = Mock(__name__ = "callback")
    watchdog.register_handler("json_file_1.json",callback)
    async def fake_awatch(*args,**kwargs):
        yield {(getattr(Change,event), tmp_path/"json_file_1.json")}

    #Act
    with patch('src.utils.watchdog.awatch',fake_awatch):
        await watchdog._watch()

    #Assert
    getattr(callback,expected)()
@pytest.mark.parametrize("filename",[".env","file.tmp","file~","../file.json","../../file.json"])
@pytest.mark.asyncio
async def test_watch(tmp_path,filename):
    #Arrange
    json_file_1 = tmp_path/filename
    json_file_1.write_text('{}')
    watchdog = ConfigWatcher(tmp_path)
    callback = Mock(__name__ = "callback")
    watchdog.register_handler(filename,callback)
    async def fake_awatch(*args,**kwargs):
        yield {(Change.added, tmp_path/filename)}

    #Act
    with patch('src.utils.watchdog.awatch',fake_awatch):
        await watchdog._watch()

    #Assert
    callback.assert_not_called()
