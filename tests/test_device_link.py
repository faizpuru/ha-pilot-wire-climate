"""Tests for linking the climate entity to the source device."""
import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pilot_wire_climate.const import (
    CONF_DEFAULT_PRESET, CONF_PRESET, DOMAIN)

OPTIONS = ["off", "frost_protection", "eco", "comfort", "comfort_-1", "comfort_-2"]


@pytest.fixture
async def source(hass, mqtt_mock):
    """A Zigbee-like device owned by another config entry, with a select."""
    src_entry = MockConfigEntry(domain="mqtt", data={})
    src_entry.add_to_hass(hass)
    dev_reg, ent_reg = dr.async_get(hass), er.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id=src_entry.entry_id,
        identifiers={("mqtt", "zigbee2mqtt_0x01")},
        name="Radiateur salon",
    )
    select = ent_reg.async_get_or_create(
        "select", "mqtt", "0x01_pilot_wire", config_entry=src_entry,
        device_id=device.id, suggested_object_id="radiateur_salon_pilot_wire",
    )
    hass.states.async_set(select.entity_id, "comfort", {"options": OPTIONS})
    return src_entry, device, select


def helper_entry(hass, select_id, minor_version=3, **options):
    entry = MockConfigEntry(
        domain=DOMAIN, title="Radiateur salon", version=1,
        minor_version=minor_version,
        options={CONF_PRESET: select_id, **options},
    )
    entry.add_to_hass(hass)
    return entry


async def setup(hass, entry):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED


def climate_entry(hass, entry):
    entities = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    assert len(entities) == 1
    return entities[0]


def helper_devices(hass, entry):
    return dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)


async def test_new_entry_links_to_source_device(hass, source, caplog):
    _, device, select = source
    entry = helper_entry(hass, select.entity_id, default_preset="comfort")
    await setup(hass, entry)

    assert climate_entry(hass, entry).device_id == device.id
    assert helper_devices(hass, entry) == []
    assert hass.states.get(climate_entry(hass, entry).entity_id) is not None
    assert "deprecated" not in caplog.text


async def test_migration_removes_duplicate_device(hass, source, caplog):
    _, device, select = source
    entry = helper_entry(hass, select.entity_id, minor_version=2,
                         default_preset="comfort")
    dev_reg, ent_reg = dr.async_get(hass), er.async_get(hass)
    # Duplicate created by the old device_info that copied the identifiers
    duplicate = dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={("mqtt", "zigbee2mqtt_0x01")},
    )
    assert duplicate.id != device.id
    ent_reg.async_get_or_create(
        "climate", DOMAIN, entry.entry_id, config_entry=entry,
        device_id=duplicate.id,
    )

    await setup(hass, entry)

    assert entry.minor_version == 3
    assert dev_reg.async_get(duplicate.id) is None
    assert dev_reg.async_get(device.id) is not None
    assert climate_entry(hass, entry).device_id == device.id
    assert "deprecated" not in caplog.text


@pytest.mark.parametrize(
    ("old", "new"),
    [(None, "comfort"), ("away", "frost_protection"), ("bogus", "comfort"),
     ("eco", "eco")],
)
async def test_migration_default_preset(hass, source, old, new):
    _, _, select = source
    opts = {} if old is None else {CONF_DEFAULT_PRESET: old}
    entry = helper_entry(hass, select.entity_id, minor_version=1, **opts)
    await setup(hass, entry)
    assert entry.options[CONF_DEFAULT_PRESET] == new
    assert entry.minor_version == 3


async def test_source_entity_renamed(hass, source):
    _, device, select = source
    entry = helper_entry(hass, select.entity_id, default_preset="comfort")
    await setup(hass, entry)

    er.async_get(hass).async_update_entity(
        select.entity_id, new_entity_id="select.radiateur_renomme")
    hass.states.async_set("select.radiateur_renomme", "eco", {"options": OPTIONS})
    await hass.async_block_till_done()

    assert entry.options[CONF_PRESET] == "select.radiateur_renomme"
    assert entry.state is ConfigEntryState.LOADED
    climate = climate_entry(hass, entry)
    assert climate.device_id == device.id
    assert hass.states.get(climate.entity_id).attributes["preset_mode"] == "eco"


async def test_source_entity_moved_to_other_device(hass, source):
    src_entry, _, select = source
    entry = helper_entry(hass, select.entity_id, default_preset="comfort")
    await setup(hass, entry)

    other = dr.async_get(hass).async_get_or_create(
        config_entry_id=src_entry.entry_id,
        identifiers={("mqtt", "zigbee2mqtt_0x02")}, name="Radiateur chambre",
    )
    er.async_get(hass).async_update_entity(select.entity_id, device_id=other.id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert climate_entry(hass, entry).device_id == other.id
    assert helper_devices(hass, entry) == []


async def test_yaml_entity_has_no_device(hass, source, caplog):
    _, _, select = source
    assert await async_setup_component(hass, "climate", {"climate": [
        {"platform": DOMAIN, "presets": select.entity_id, "unique_id": "yaml1"}
    ]})
    await hass.async_block_till_done()

    entity_id = er.async_get(hass).async_get_entity_id("climate", DOMAIN, "yaml1")
    assert entity_id is not None
    assert er.async_get(hass).async_get(entity_id).device_id is None
    assert "without a config entry" not in caplog.text
