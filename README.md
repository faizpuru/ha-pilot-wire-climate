# README - Pilot Wire Integration for Home Assistant

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/faizpuru/ha-pilot-wire-climate/blob/master/README.md)
[![fr](https://img.shields.io/badge/lang-fr-blue.svg)](https://github.com/faizpuru/ha-pilot-wire-climate/blob/master/README-fr.md)

## Overview
This Home Assistant integration simplifies the setup of pilot wire modules for heating systems, providing seamless conversion of multiple entities (`select` and `power`) into a unified `climate` entity. An optional temperature `sensor` entity can also be added. This integration is ideal for controlling pilot wire heating modules, enabling streamlined control and monitoring of heating states.

### Key Features
- Converts `select` and `power` entities into a single `climate` entity.
- Utilizes the `select` entity to adjust the pilot wire preset modes.
- Uses the `power` entity to detect whether the heating is on or off.
- Configurable power threshold to determine heating state.
- Configurable default power on preset.
- Optional support for temperature `sensor` entities.

### Compatibility
The integration is compatible with the following devices or any climate manageable with a select entity :
- **Equation**: SIN-4-FP-21_EQU
- **Legrand**: 064882
- **NodOn**: SIN-4-FP-20, SIN-4-FP-21

## Installation

### Option 1: Using HACS (Home Assistant Community Store)
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=faizpuru&repository=ha-pilot-wire-climate&category=integration)

1. Use the button above or search for "Wire Pilot Climate" in HACS
2. Download the integration and restart Home Assistant

### Option 2: Manual Installation
1. Copy the integration files to your Home Assistant custom components directory.
2. Restart Home Assistant.
3. Add the integration through the Home Assistant UI or by modifying the `configuration.yaml` file.

## Configuration
To set up this integration, you can either add it through the Home Assistant UI or configure it manually. Below is a sample `configuration.yaml` setup.

> [!IMPORTANT]  
> This integration is implemented as a **Helper** in Home Assistant and is not a full-fledged custom integration. 
> 
> To initialize this helper, follow this path in your Home Assistant interface:
> 1. Settings
> 2. Devices and Services
> 3. Helpers
> 4. Create Helper
> 5. Pilot Wire Thermostat
>
> Once configured, the climate entity will appear in the Helpers tab. It will be automatically linked to the device of the select entity you chose during setup.


## YAML configuration

If you prefer to use `yaml`, you can, but it's not recommended as more and more integrations are moved to the UI. All the options are available in the UI.

| Key                | Type    | Required | Description                                                                                                               |
| :----------------- | :------ | :------- | :------------------------------------------------------------------------------------------------------------------------ |
| `platform`         | string  | yes      | pilot_wire_climate                                                                                                        |
| `presets`          | string  | yes      | Select entity id to adjust the pilot wire preset modes                                                                    |
| `power`            | string  | no       | Power sensor to detect whether the heating is on or off                                                                   |
| `temperature`      | string  | no       | Temperature sensor id (for display)                                                                                       |
| `additional_modes` | boolean | no       | 6-order support (add Comfort -1 and Comfort -2 preset)                                                                    |
| `power_threshold`  | integer | no       | Power threshold (in watts) above which the heater is considered to be heating                                             |
| `default_preset`   | string  | no       | Default 'power on' preset  from "frost_protection", "eco", "comfort-2", "comfort-1" "comfort"                                                                        |
| `name`             | string  | no       | Name to use in the frontend                                                                                               |
| `unique_id`        | string  | no       | An ID that uniquely identifies this climate. If two climates have the same unique ID, Home Assistant will raise an error  |


The unique id is recommended to allow icon, entity_id or name changes from the UI.

```yaml
climate:
  - platform: pilot_wire_climate
    name: Living Room Heater
    unique_id: living_room_heater_climate
    presets: select.heater_preset
    power: sensor.heater_power
    power_threshold: 10
    temperature: sensor.living_room_temperature
    default_preset: eco
    additional_modes: true
  ```

## 🤝 Contributing

Contributions are welcome! Feel free to:
- 🐛 Report bugs
- 💡 Suggest improvements
- 🔀 Submit pull requests

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---
If you find this integration helpful, please consider giving it a ⭐️ on GitHub!
