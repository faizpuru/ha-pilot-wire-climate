# README - Pilot Wire Integration for Home Assistant

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/faizpuru/ha-pilot-wire-climate/blob/master/README.md)
[![fr](https://img.shields.io/badge/lang-fr-blue.svg)](https://github.com/faizpuru/ha-pilot-wire-climate/blob/master/README-fr.md)

## Overview
This Home Assistant integration simplifies the setup of pilot wire modules for heating systems, providing seamless conversion of multiple entities (`select` and `power`) into a unified `climate` entity. An optional temperature `sensor` entity can also be added. This integration is ideal for controlling pilot wire heating modules, enabling streamlined control and monitoring of heating states.

### Key Features
- Converts `select` and `power` entities into a single `climate` entity.
- Utilizes the `select` entity to adjust the pilot wire preset modes.
- Uses the `power` entity to detect whether the heating is on or off.
- Optional support for temperature `sensor` entities.

### Compatibility
The integration is compatible with the following devices or any climate manageable with a select entity :
- **Equation**: SIN-4-FP-21_EQU
- **Legrand**: 064882
- **NodOn**: SIN-4-FP-20, SIN-4-FP-21

## Installation

### Option 1: Using HACS (Home Assistant Community Store)
1. Go to HACS in Home Assistant.
2. Click on "Integrations" and select the three-dot menu in the top-right corner.
3. Select "Custom repositories."
4. Add the following repository URL: `https://github.com/faizpuru/ha-pilot-wire-climate`
5. Choose "Integration" as the category.
6. Install the integration, then restart Home Assistant.

### Option 2: Manual Installation
1. Copy the integration files to your Home Assistant custom components directory.
2. Restart Home Assistant.
3. Add the integration through the Home Assistant UI or by modifying the `configuration.yaml` file.

## Configuration
To set up this integration, you can either add it through the Home Assistant UI or configure it manually. Below is a sample `configuration.yaml` setup.

## YAML configuration

If you prefer to use `yaml`, you can, but it's not recommended as more and more integrations are moved to the UI. All the options are available in the UI.

| Key                | Type    | Required | Description                                                                                                               |
| :----------------- | :------ | :------- | :------------------------------------------------------------------------------------------------------------------------ |
| `platform`         | string  | yes      | pilot_wire_climate                                                                                                        |
| `presets`          | string  | yes      | Select entity id to adjust the pilot wire preset modes                                                                    |
| `power`            | string  | no       | Power sensor to detect whether the heating is on or off                                                                   |
| `temperature`      | string  | no       | Temperature sensor id (for display)                                                                                       |
| `additional_modes` | boolean | no       | 6-order support (add Comfort -1 and Comfort -2 preset)                                                                    |
| `name`             | string  | no       | Name to use in the frontend.                                                                                              |
| `unique_id`        | string  | no       | An ID that uniquely identifies this climate. If two climates have the same unique ID, Home Assistant will raise an error. |

The unique id is recommended to allow icon, entity_id or name changes from the UI.

```yaml
climate:
  - platform: pilot_wire_climate
    name: Living Room Heater
    unique_id: living_room_heater_climate
    presets: select.heater_preset
    power: sensor.heater_power
    temperature: sensor.living_room_temperature
    additional_modes: true