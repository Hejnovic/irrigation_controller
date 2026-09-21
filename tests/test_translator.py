import pytest
from unittest.mock import Mock, call, patch, MagicMock
from src.utils.translator import Translator
from pathlib import Path

def test_translator_loads_translations_from_dir(tmp_path):
    #Arrange
    locales_dir = tmp_path/"locales"
    locales_dir.mkdir()
    json_file_1 = tmp_path/"locales/en.json"
    json_file_1.write_text('{}')
    json_file_2 = tmp_path/"locales/pl.json"
    json_file_2.write_text('{}')
    

    #Act
    translator = Translator(tmp_path/"locales")

    #Assert
    assert len(translator._translations) == 2

def test_translator_set_locale(tmp_path):
    #Arrange
    locales_dir = tmp_path/"locales"
    locales_dir.mkdir()
    json_file_1 = tmp_path/"locales/en.json"
    json_file_1.write_text('{}')
    json_file_2 = tmp_path/"locales/pl.json"
    json_file_2.write_text('{}')
    translator = Translator(tmp_path/"locales")

    #Act
    translator.set_locale("pl")

    #Assert
    assert translator._locale == "pl"

def test_translate_no_kwargs(tmp_path):
    #Arrange
    locales_dir = tmp_path/"locales"
    locales_dir.mkdir()
    json_file_1 = tmp_path/"locales/test.json"
    json_file_1.write_text('{"hello":"test"}')
    translator = Translator(tmp_path/"locales")
    translator.set_locale("test")

    #Act
    translation = translator.translate("hello")

    #Assert
    assert translation == "test"

def test_translate_with_kwargs(tmp_path):
    #Arrange
    locales_dir = tmp_path/"locales"
    locales_dir.mkdir()
    json_file_1 = tmp_path/"locales/test.json"
    json_file_1.write_text('{"hello":"test {kwarg1} {kwarg2}"}')
    translator = Translator(tmp_path/"locales")
    translator.set_locale("test")

    #Act
    translation = translator.translate("hello",kwarg1="test1",kwarg2="test2")

    #Assert
    assert translation == "test test1 test2"

def test_translate_on_not_existing_key(tmp_path):
    #Arrange
    locales_dir = tmp_path/"locales"
    locales_dir.mkdir()
    json_file_1 = tmp_path/"locales/test.json"
    json_file_1.write_text('{"hello":"test"}')
    translator = Translator(tmp_path/"locales")
    translator.set_locale("test")

    #Act
    translation = translator.translate("welcome")

    #Assert
    assert translation == "welcome"

def test_translate_on_not_existing_kwargs(tmp_path):
    #Arrange
    locales_dir = tmp_path/"locales"
    locales_dir.mkdir()
    json_file_1 = tmp_path/"locales/test.json"
    json_file_1.write_text('{"hello":"test"}')
    translator = Translator(tmp_path/"locales")
    translator.set_locale("test")

    #Act
    translation = translator.translate("hello",kwarg="not_exist")

    #Assert
    assert translation == "test"

def test_translate_with_too_many_kwargs(tmp_path):
    #Arrange
    locales_dir = tmp_path/"locales"
    locales_dir.mkdir()
    json_file_1 = tmp_path/"locales/test.json"
    json_file_1.write_text('{"hello":"test {kwarg1} {kwarg2}"}')
    translator = Translator(tmp_path/"locales")
    translator.set_locale("test")

    #Act
    translation = translator.translate("hello",kwarg1="test1",kwarg2="test2",kwarg3="test3")

    #Assert
    assert translation == "test test1 test2"

def test_translate_with_not_supplied_kwargs(tmp_path):
    #Arrange
    locales_dir = tmp_path/"locales"
    locales_dir.mkdir()
    json_file_1 = tmp_path/"locales/test.json"
    json_file_1.write_text('{"hello":"test {kwarg1} {kwarg2}"}')
    translator = Translator(tmp_path/"locales")
    translator.set_locale("test")

    #Act
    translation = translator.translate("hello",kwarg1="test1")

    #Assert
    assert translation == "test {kwarg1} {kwarg2}"

def test_translate_with__not_all_kwargs_supplied(tmp_path):
    #Arrange
    locales_dir = tmp_path/"locales"
    locales_dir.mkdir()
    json_file_1 = tmp_path/"locales/test.json"
    json_file_1.write_text('{"hello":"test {kwarg1} {kwarg2}"}')
    translator = Translator(tmp_path/"locales")
    translator.set_locale("test")

    #Act
    translation = translator.translate("hello",kwarg1="test1")

    #Assert
    assert translation == "test {kwarg1} {kwarg2}"