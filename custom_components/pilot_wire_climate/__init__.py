""" Pilot wire component."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device import \
    async_remove_stale_devices_links_keep_entity_device
from .const import CONF_DEFAULT_PRESET, CONF_PRESET, DEFAULT_DEFAULT_PRESET, DOMAIN, VALUES_MAPPING, OLD_PRESET_VALUE_MAPPING

PLATFORMS = [Platform.CLIMATE]
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""

    async_remove_stale_devices_links_keep_entity_device(
        hass,
        entry.entry_id,
        entry.options[CONF_PRESET],
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(
        config_entry_update_listener))
    return True


async def config_entry_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener, called when the config entry options are changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass, config_entry: ConfigEntry):
    default_preset = config_entry.options.get(CONF_DEFAULT_PRESET)
    if default_preset is None:
        update_default_preset(DEFAULT_DEFAULT_PRESET, hass, config_entry)
    elif default_preset not in VALUES_MAPPING:
        update_default_preset(
            OLD_PRESET_VALUE_MAPPING[default_preset], hass, config_entry)
    return True


def update_default_preset(default_preset, hass, config_entry):
    options_v2 = {**config_entry.options}
    options_v2[CONF_DEFAULT_PRESET] = default_preset
    hass.config_entries.async_update_entry(
        config_entry, data=config_entry.data, options=options_v2)
