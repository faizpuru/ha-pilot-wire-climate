"""Tests for the climate entity when the select entity misbehaves."""
import pytest
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.exceptions import ServiceValidationError
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.pilot_wire_climate.const import DOMAIN

SELECT = "select.radiateur"
CLIMATE = "climate.radiateur"
FOUR_ORDERS = ["off", "frost_protection", "eco", "comfort"]
SIX_ORDERS = FOUR_ORDERS + ["comfort_-1", "comfort_-2"]


async def setup_climate(hass, **config):
    """Set up the climate and return the calls made to the select entity."""
    assert await async_setup_component(hass, "climate", {"climate": [
        {"platform": DOMAIN, "name": "Radiateur", "presets": SELECT, **config}
    ]})
    await hass.async_block_till_done()
    # Mocked after setup, which loads the real select service
    return async_mock_service(hass, "select", "select_option")


async def call(hass, service, **data):
    await hass.services.async_call(
        "climate", service, {"entity_id": CLIMATE, **data}, blocking=True)


async def test_four_order_module_hides_additional_presets(hass):
    hass.states.async_set(SELECT, "comfort", {"options": FOUR_ORDERS})
    select_option = await setup_climate(
        hass, additional_modes=True, default_preset="comfort-1")

    state = hass.states.get(CLIMATE)
    assert state.attributes["preset_modes"] == ["comfort", "eco", "away", "none"]

    # The default preset is missing, so turning on falls back to Comfort
    await call(hass, "set_hvac_mode", hvac_mode="heat")
    assert select_option[-1].data["option"] == "comfort"


async def test_six_order_module(hass):
    hass.states.async_set(SELECT, "comfort_-2", {"options": SIX_ORDERS})
    select_option = await setup_climate(hass, default_preset="comfort-1")

    state = hass.states.get(CLIMATE)
    assert state.attributes["preset_modes"] == [
        "comfort", "comfort_1", "comfort_2", "eco", "away", "none"]
    assert state.attributes["preset_mode"] == "comfort_2"

    await call(hass, "set_hvac_mode", hvac_mode="heat")
    assert select_option[-1].data["option"] == "comfort_-1"
    await call(hass, "set_preset_mode", preset_mode="away")
    assert select_option[-1].data["option"] == "frost_protection"
    await call(hass, "set_hvac_mode", hvac_mode="off")
    assert select_option[-1].data["option"] == "off"


async def test_missing_option_raises(hass):
    hass.states.async_set(SELECT, "comfort", {"options": ["comfort", "eco"]})
    select_option = await setup_climate(hass, additional_modes=False)

    with pytest.raises(ServiceValidationError):
        await call(hass, "set_hvac_mode", hvac_mode="off")
    assert select_option == []


async def test_follows_select_availability(hass):
    hass.states.async_set(SELECT, "eco", {"options": FOUR_ORDERS})
    await setup_climate(hass)
    assert hass.states.get(CLIMATE).attributes["preset_mode"] == "eco"

    hass.states.async_set(SELECT, STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    assert hass.states.get(CLIMATE).state == STATE_UNAVAILABLE

    hass.states.async_set(SELECT, "off", {"options": FOUR_ORDERS})
    await hass.async_block_till_done()
    state = hass.states.get(CLIMATE)
    assert state.state == "off"
    assert state.attributes["preset_mode"] == "none"


async def test_select_without_options(hass):
    hass.states.async_set(SELECT, "comfort")
    await setup_climate(hass)
    assert hass.states.get(CLIMATE).state == "heat"


async def test_unknown_options_are_ignored(hass):
    hass.states.async_set(SELECT, "comfort", {"options": FOUR_ORDERS + ["bogus"]})
    await setup_climate(hass, additional_modes=False)
    assert hass.states.get(CLIMATE).attributes["preset_modes"] == [
        "comfort", "eco", "away", "none"]
