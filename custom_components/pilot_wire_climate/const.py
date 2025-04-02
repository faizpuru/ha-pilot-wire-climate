from homeassistant.components.climate import (PRESET_AWAY, PRESET_COMFORT,
                                              PRESET_ECO)

DOMAIN = "pilot_wire_climate"
DEFAULT_NAME = "Thermostat"
CONF_PRESET = "presets"
CONF_TEMP = "temperature"
CONF_POWER = "power"
CONF_ADDITIONAL_MODES = "additional_modes"
CONF_POWER_THRESHOLD = "power_threshold"
PRESET_COMFORT_1 = "comfort_1"
PRESET_COMFORT_2 = "comfort_2"
CONF_DEFAULT_PRESET = "default_preset"

VALUE_OFF = "off"
VALUE_FROST = "frost_protection"
VALUE_ECO = "eco"
VALUE_COMFORT_2 = "comfort-2"
VALUE_COMFORT_1 = "comfort-1"
VALUE_COMFORT = "comfort"
DEFAULT_DEFAULT_PRESET = VALUE_COMFORT


OLD_PRESET_VALUE_MAPPING = {
    PRESET_COMFORT: VALUE_COMFORT,
    PRESET_COMFORT_1: VALUE_COMFORT_1,
    PRESET_COMFORT_2: VALUE_COMFORT_2,
    PRESET_ECO: VALUE_ECO,
    PRESET_AWAY: VALUE_FROST
}

VALUES_MAPPING = {
    VALUE_OFF: ["off", "Off"],
    VALUE_FROST: ["frost_protection", "FrostProtection"],
    VALUE_ECO: ["eco", "Eco"],
    VALUE_COMFORT: ["comfort", "Comfort"],
    VALUE_COMFORT_2: ["comfort_-2", "ComfortMinus2"],
    VALUE_COMFORT_1: ["comfort_-1", "ComfortMinus1"],
}
