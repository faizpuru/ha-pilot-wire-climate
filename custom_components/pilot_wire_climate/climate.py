"""Platform for Pilot Wire."""

import logging
import math

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.climate import \
    PLATFORM_SCHEMA as CLIMATE_PLATFORM_SCHEMA
from homeassistant.components.climate import (PRESET_AWAY, PRESET_COMFORT,
                                              PRESET_ECO, PRESET_NONE,
                                              ClimateEntity,
                                              ClimateEntityFeature, HVACAction,
                                              HVACMode)
from homeassistant.components.select import DOMAIN as SELECT_DOMAIN
from homeassistant.components.select import SERVICE_SELECT_OPTION
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (ATTR_ENTITY_ID, CONF_NAME, CONF_UNIQUE_ID,
                                 EVENT_HOMEASSISTANT_START, STATE_UNAVAILABLE,
                                 STATE_UNKNOWN, UnitOfTemperature)
from homeassistant.core import (CoreState, Event, EventStateChangedData,
                                HomeAssistant, State, callback)
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device import async_entity_id_to_device
from homeassistant.helpers.device_registry import AnyDeviceEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.reload import async_setup_reload_service
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import DOMAIN, PLATFORMS
from .util import get_value_key
from .const import (CONF_ADDITIONAL_MODES,
                    CONF_POWER,
                    CONF_POWER_THRESHOLD,
                    CONF_PRESET,
                    CONF_TEMP,
                    CONF_HUMIDITY,
                    DEFAULT_NAME,
                    PRESET_COMFORT_1,
                    PRESET_COMFORT_2,
                    CONF_DEFAULT_PRESET,
                    DEFAULT_DEFAULT_PRESET, VALUE_COMFORT, VALUE_COMFORT_1, VALUE_COMFORT_2, VALUE_ECO, VALUE_FROST, VALUE_OFF, VALUES_MAPPING)

_LOGGER = logging.getLogger(__name__)

PRESET_VALUES = {
    PRESET_COMFORT: VALUE_COMFORT,
    PRESET_COMFORT_1: VALUE_COMFORT_1,
    PRESET_COMFORT_2: VALUE_COMFORT_2,
    PRESET_ECO: VALUE_ECO,
    PRESET_AWAY: VALUE_FROST,
    PRESET_NONE: VALUE_OFF,
}
ADDITIONAL_VALUES = (VALUE_COMFORT_1, VALUE_COMFORT_2)


PLATFORM_SCHEMA_COMMON = vol.Schema(
    {
        vol.Required(CONF_PRESET): cv.entity_id,
        vol.Optional(CONF_TEMP): cv.entity_id,
        vol.Optional(CONF_HUMIDITY): cv.entity_id,
        vol.Optional(CONF_POWER): cv.entity_id,
        vol.Optional(CONF_ADDITIONAL_MODES, default=True): cv.boolean,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Optional(CONF_POWER_THRESHOLD): cv.positive_float,
        vol.Optional(CONF_DEFAULT_PRESET, default=DEFAULT_DEFAULT_PRESET): vol.In([VALUE_COMFORT, VALUE_COMFORT_1, VALUE_COMFORT_2, VALUE_ECO, VALUE_FROST]),
    }
)

PLATFORM_SCHEMA = CLIMATE_PLATFORM_SCHEMA.extend(PLATFORM_SCHEMA_COMMON.schema)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize config entry."""
    await _async_setup_config(
        hass,
        PLATFORM_SCHEMA_COMMON(dict(config_entry.options)),
        config_entry.entry_id,
        async_add_entities,
        device=async_entity_id_to_device(
            hass, config_entry.options[CONF_PRESET]),
    )


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the generic thermostat platform."""

    await async_setup_reload_service(hass, DOMAIN, PLATFORMS)
    await _async_setup_config(
        hass, config, config.get(CONF_UNIQUE_ID), async_add_entities
    )


async def _async_setup_config(
    hass: HomeAssistant,
    config: ConfigType,
    unique_id: str | None,
    async_add_entities: AddEntitiesCallback,
    device: AnyDeviceEntry | None = None,
) -> None:
    """Set up the pilot wire climate platform."""
    name: str | None = config.get(CONF_NAME)
    preset_entity_id: str = config.get(CONF_PRESET)
    temp_entity_id: str | None = config.get(CONF_TEMP)
    humidity_entity_id: str | None = config.get(CONF_HUMIDITY)
    power_entity_id: str | None = config.get(CONF_POWER)
    additional_modes: bool = config.get(CONF_ADDITIONAL_MODES)
    power_threshold: float = config.get(CONF_POWER_THRESHOLD)
    default_preset: str | None = config.get(CONF_DEFAULT_PRESET)

    async_add_entities(
        [
            PilotWireClimate(
                hass,
                name,
                preset_entity_id,
                temp_entity_id,
                humidity_entity_id,
                power_entity_id,
                additional_modes,
                power_threshold,
                default_preset,
                unique_id,
                device,
            )
        ]
    )


class PilotWireClimate(ClimateEntity):
    """Representation of a Pilot Wire device."""

    _attr_should_poll = False
    _attr_translation_key: str = "pilot_wire"
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(
        self,
        hass: HomeAssistant,
        name: str | None,
        preset_entity_id: str,
        temp_entity_id: str | None,
        humidity_entity_id: str | None,
        power_entity_id: str | None,
        additional_modes: bool,
        power_threshold: float,
        default_preset: str,
        unique_id: str | None,
        device: AnyDeviceEntry | None = None,
    ) -> None:
        """Initialize the climate device."""

        registry = er.async_get(hass)
        preset_entity = registry.async_get(preset_entity_id)
        self.options_dict: dict[str, str] = {}
        has_entity_name = preset_entity.has_entity_name if preset_entity else False

        self.device_entry = device

        if name:
            self._attr_name = name
        else:
            self._attr_name = DEFAULT_NAME

        self.preset_entity_id = preset_entity_id
        self.temp_entity_id = temp_entity_id
        self.humidity_entity_id = humidity_entity_id
        self.power_entity_id = power_entity_id
        self.additional_modes = additional_modes
        self._power_threshold = power_threshold
        self._cur_temperature = None
        self._cur_humidity = None
        self._cur_power = None
        self._cur_mode = None
        self._default_preset = default_preset

        self._attr_has_entity_name = has_entity_name
        self._attr_unique_id = (
            unique_id if unique_id else "pilot_wire_" + preset_entity_id
        )

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        # Add listener
        if self.temp_entity_id is not None:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [
                        self.temp_entity_id], self._async_temp_changed
                )
            )

        if self.humidity_entity_id is not None:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [
                        self.humidity_entity_id], self._async_humidity_changed
                )
            )

        if self.power_entity_id is not None:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [
                        self.power_entity_id], self._async_power_changed
                )
            )

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self.preset_entity_id], self._async_mode_changed
            )
        )

        @callback
        def _async_startup(_: Event | None = None) -> None:
            """Init on startup."""
            mode_state = self.hass.states.get(self.preset_entity_id)
            if mode_state and mode_state.state not in (
                STATE_UNAVAILABLE,
                STATE_UNKNOWN,
            ):
                self._async_update_mode(mode_state)
                self.async_write_ha_state()

            if self.temp_entity_id is not None:
                temp_state = self.hass.states.get(self.temp_entity_id)
                if temp_state and temp_state.state not in (
                    STATE_UNAVAILABLE,
                    STATE_UNKNOWN,
                ):
                    self._async_update_temp(temp_state)
                    self.async_write_ha_state()

            if self.humidity_entity_id is not None:
                humidity_state = self.hass.states.get(self.humidity_entity_id)
                if humidity_state and humidity_state.state not in (
                    STATE_UNAVAILABLE,
                    STATE_UNKNOWN,
                ):
                    self._async_update_humidity(humidity_state)
                    self.async_write_ha_state()

            if self.power_entity_id is not None:
                power_state = self.hass.states.get(self.power_entity_id)
                if power_state and power_state.state not in (
                    STATE_UNAVAILABLE,
                    STATE_UNKNOWN,
                ):
                    self._async_update_power(power_state)
                    self.async_write_ha_state()

        if self.hass.state is CoreState.running:
            _async_startup()
        else:
            self.hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_START, _async_startup)

    @property
    def available(self) -> bool:
        """Return whether the select entity is available."""
        state = self.hass.states.get(self.preset_entity_id)
        return state is not None and state.state not in (
            STATE_UNAVAILABLE,
            STATE_UNKNOWN,
        )

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return the list of supported features."""
        return (
            ClimateEntityFeature.PRESET_MODE
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TURN_ON
        )

    def update(self) -> None:
        """Update unit attributes."""

    @property
    def hvac_action(self) -> str:
        """Return the current heating action from the power sensor."""
        value = None
        if self._cur_power is not None:
            if self._cur_power > self.power_threshold:
                value = HVACAction.HEATING
            elif self.preset_mode == PRESET_NONE:
                value = HVACAction.OFF
            else:
                value = HVACAction.IDLE
        return value

    @property
    def power_threshold(self) -> float:
        """Return the power above which the heater is heating."""
        return 0 if self._power_threshold is None else self._power_threshold

    @property
    def temperature_unit(self) -> str:
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS

    @property
    def current_temperature(self) -> float | None:
        """Return the sensor temperature."""
        return self._cur_temperature

    @property
    def current_humidity(self) -> float | None:
        """Return the sensor humidity."""
        return self._cur_humidity

    # Presets

    @property
    def preset_modes(self) -> list[str] | None:
        """List the presets the select entity has an option for."""
        presets = [
            preset for preset, value in PRESET_VALUES.items()
            if self.additional_modes or value not in ADDITIONAL_VALUES
        ]
        if not self.options_dict:
            # Options are not known until the select entity is available
            return presets
        return [
            preset for preset in presets
            if PRESET_VALUES[preset] in self.options_dict
        ]

    @property
    def preset_mode(self) -> str | None:
        """Preset current mode."""
        if self._cur_mode is None:
            return None
        value = get_value_key(self._cur_mode)
        if value in ADDITIONAL_VALUES and not self.additional_modes:
            return PRESET_COMFORT
        return next(
            (preset for preset, v in PRESET_VALUES.items() if v == value),
            PRESET_COMFORT,
        )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set preset mode."""
        value = self.get_preset_value(preset_mode)
        await self._async_set_mode_value(value)

    def get_preset_value(self, preset_mode) -> str:
        """Return the select option for a preset."""
        return self._get_option(PRESET_VALUES.get(preset_mode))

    def _get_option(self, value: str | None) -> str:
        """Return the select option for a pilot wire order."""
        if value not in self.options_dict:
            raise ServiceValidationError(
                f"{self.preset_entity_id} has no option for {value}")
        return self.options_dict[value]
    # Modes

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """List of available operation modes."""
        return [HVACMode.HEAT, HVACMode.OFF]

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.HEAT:
            # Fall back to Comfort when the select has no default preset option
            default = self._default_preset
            if default not in self.options_dict:
                default = VALUE_COMFORT
            value = self._get_option(default)
        else:
            value = self._get_option(VALUE_OFF)
        await self._async_set_mode_value(value)

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return hvac operation ie. heat, off mode."""
        if self.preset_mode is not None:
            return HVACMode.OFF if self.preset_mode == PRESET_NONE else HVACMode.HEAT
        return None

    async def _async_temp_changed(self, event: Event[EventStateChangedData]) -> None:
        """Handle temperature changes."""
        new_state = event.data["new_state"]
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return

        self._async_update_temp(new_state)
        self.async_write_ha_state()

    async def _async_power_changed(self, event: Event[EventStateChangedData]) -> None:
        """Handle power changes."""
        new_state = event.data["new_state"]
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return
        self._async_update_power(new_state)
        self.async_write_ha_state()

    @callback
    def _async_mode_changed(self, event: Event[EventStateChangedData]) -> None:
        """Handle preset switch state changes."""

        new_state = event.data["new_state"]
        # Also write the state when the select goes away, to report unavailable
        if new_state is not None and new_state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            self._async_update_mode(new_state)
        self.async_write_ha_state()

    @callback
    def _async_update_mode(self, state: State):
        self._cur_mode = state.state
        self.options_dict = {
            value: option
            for option in state.attributes.get("options") or []
            if (value := get_value_key(option)) is not None
        }

    @callback
    def _async_update_temp(self, state: State):
        try:
            cur_temp = float(state.state)
            if not math.isfinite(cur_temp):
                raise ValueError(f"Sensor has illegal state {state.state}")
            self._cur_temperature = cur_temp
        except ValueError as ex:
            _LOGGER.error("Unable to update from temperature sensor: %s", ex)

    async def _async_humidity_changed(self, event: Event[EventStateChangedData]) -> None:
        """Handle humidity changes."""
        new_state = event.data["new_state"]
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return

        self._async_update_humidity(new_state)
        self.async_write_ha_state()

    @callback
    def _async_update_humidity(self, state: State):
        try:
            cur_humidity = float(state.state)
            if not math.isfinite(cur_humidity):
                raise ValueError(f"Sensor has illegal state {state.state}")
            self._cur_humidity = cur_humidity
        except ValueError as ex:
            _LOGGER.error("Unable to update from humidity sensor: %s", ex)

    @callback
    def _async_update_power(self, state: State):
        try:
            cur_power = float(state.state)
            if not math.isfinite(cur_power):
                raise ValueError(f"Sensor has illegal state {state.state}")
            self._cur_power = cur_power
        except ValueError as ex:
            _LOGGER.error("Unable to update from power sensor: %s", ex)

    async def _async_set_mode_value(self, value):
        data = {
            ATTR_ENTITY_ID: self.preset_entity_id,
            "option": value,
        }
        await self.hass.services.async_call(SELECT_DOMAIN, SERVICE_SELECT_OPTION, data)
