from unittest.mock import Mock, call, AsyncMock, patch
from pathlib import Path
import pytest
from src.utils.watchdog import Watchdog
import asyncio
from watchfiles import Change
## INNIT TEST
def test_innit_gather_all_config_files(tmp_path):
    #Arrange
    json_file_1 = tmp_path/"json_file_1.json"
    json_file_1.write_text('{}')

    #Act
    watchdog = Watchdog(tmp_path)

    #Assert
    assert len(watchdog._config_files) == 1

## REGISTER HANDLER TESTS
def test_register_handler_adds_callback_to_config_file(tmp_path):
    #Arrange
    json_file_1 = tmp_path/"json_file_1.json"
    json_file_1.write_text('{}')
    watchdog = Watchdog(tmp_path)
    callback = Mock(__name__ = "callback")

    #Act
    watchdog.register_handler("json_file_1.json",callback)

    #Assert
    watchdog._handlers[json_file_1] == callback

def test_register_handler_does_nothing_when_file_does_not_exist(tmp_path):
    #Arrange
    json_file_1 = tmp_path/"json_file_1.json"
    json_file_1.write_text('{}')
    watchdog = Watchdog(tmp_path)
    callback = Mock(__name__ = "callback")

    #Act
    watchdog.register_handler("json_file_2.json",callback)

    #Assert
    assert len(watchdog._handlers) == 0

## START TESTS

def test_preload_config_calls_handlers(tmp_path):
    #Arrange
    json_file_1 = tmp_path/"json_file_1.json"
    json_file_1.write_text('{}')
    watchdog = Watchdog(tmp_path)
    watchdog.watch = AsyncMock()
    callback = Mock(__name__ = "callback")
    watchdog.register_handler("json_file_1.json",callback)


    #Act
    watchdog._preload_configs()

    #Assert
    callback.assert_called_with(tmp_path/"json_file_1.json")

## WATCH TESTS
@pytest.mark.parametrize("event,expected",[("modified","assert_called_once"),("added","assert_not_called"),("deleted","assert_not_called"),])
@pytest.mark.asyncio
async def test_watch_on_event(tmp_path,event,expected):
    #Arrange
    json_file_1 = tmp_path/"json_file_1.json"
    json_file_1.write_text('{}')
    watchdog = Watchdog(tmp_path)
    callback = Mock(__name__ = "callback")
    watchdog.register_handler("json_file_1.json",callback)
    async def fake_awatch(*args,**kwargs):
        yield {(getattr(Change,event), tmp_path/"json_file_1.json")}

    #Act
    with patch('src.utils.watchdog.awatch',fake_awatch):
        await watchdog.watch()

    #Assert
    getattr(callback,expected)()

@pytest.mark.parametrize("filename",[".env","file.tmp","file~","../file.json","../../file.json"])
@pytest.mark.asyncio
async def test_watch_on_file_name(tmp_path,filename):
    #Arrange
    json_file_1 = tmp_path/filename
    json_file_1.write_text('{}')
    watchdog = Watchdog(tmp_path)
    callback = Mock(__name__ = "callback")
    watchdog.register_handler(filename,callback)
    async def fake_awatch(*args,**kwargs):
        yield {(Change.modified, tmp_path/filename)}

    #Act
    with patch('src.utils.watchdog.awatch',fake_awatch):
        await watchdog.watch()

    #Assert
    callback.assert_not_called()

@pytest.mark.asyncio
async def test_watch_on_add_new_file(tmp_path):
    #Arrange
    watchdog = Watchdog(tmp_path)
    # json_file_1 = tmp_path/"json_file_1.json"
    # json_file_1.write_text('{}')
    watchdog._config_files = {}
    async def fake_awatch(*args,**kwargs):
        yield {(Change.added, tmp_path/"json_file_1.json")}
        yield {(Change.added, tmp_path/"json_file_2.json")}

    #Act
    with patch('src.utils.watchdog.awatch',fake_awatch):
        await watchdog.watch()

    #Assert
    assert len(watchdog._config_files) == 2

@pytest.mark.asyncio
async def test_watch_sets_callback_on_add_new_file(tmp_path):
    #Arrange
    watchdog = Watchdog(tmp_path)
    callback = Mock(__name__ = "callback1")
    watchdog.register_handler("json_file_1.json",callback)
    watchdog._config_files = {}
    async def fake_awatch(*args,**kwargs):
        yield {(Change.added, tmp_path/"json_file_1.json")}

    #Act
    with patch('src.utils.watchdog.awatch',fake_awatch):
        await watchdog.watch()

    #Assert
    assert len(watchdog._handlers) == 1
    assert len(watchdog._tracking_dict) == 0

@pytest.mark.asyncio
async def test_watch_removes_callback_on_delete_file(tmp_path):
    #Arrange
    watchdog = Watchdog(tmp_path)
    callback = Mock(__name__ = "callback1")
    watchdog._config_files = {"json_file_1.json":tmp_path/"json_file_1.json"}
    watchdog.register_handler("json_file_1.json",callback)
    async def fake_awatch(*args,**kwargs):
        yield {(Change.deleted, tmp_path/"json_file_1.json")}

    #Act
    with patch('src.utils.watchdog.awatch',fake_awatch):
        await watchdog.watch()

    #Assert
    assert len(watchdog._handlers) == 0