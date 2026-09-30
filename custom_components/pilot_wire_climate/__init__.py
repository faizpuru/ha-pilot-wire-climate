""" Pilot wire component."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device import async_entity_id_to_device_id
from homeassistant.helpers.helper_integration import async_remove_helper_devices
from .const import CONF_DEFAULT_PRESET, CONF_PRESET, DEFAULT_DEFAULT_PRESET, DOMAIN, VALUES_MAPPING, OLD_PRESET_VALUE_MAPPING

PLATFORMS = [Platform.CLIMATE]
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
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


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    if config_entry.version > 1:
        return False

    options = {**config_entry.options}
    default_preset = options.get(CONF_DEFAULT_PRESET)
    if default_preset is None:
        options[CONF_DEFAULT_PRESET] = DEFAULT_DEFAULT_PRESET
    elif default_preset not in VALUES_MAPPING:
        options[CONF_DEFAULT_PRESET] = OLD_PRESET_VALUE_MAPPING[default_preset]

    if config_entry.minor_version < 3:
        # Earlier versions put the source device's identifiers in the climate
        # entity's device_info, which leaves a duplicate of that device owned by
        # this config entry.
        async_remove_helper_devices(
            hass,
            helper_config_entry_id=config_entry.entry_id,
            source_device_id=async_entity_id_to_device_id(
                hass, options[CONF_PRESET]),
            remove_all_devices=True,
        )

    hass.config_entries.async_update_entry(
        config_entry, options=options, minor_version=3)
    return True
