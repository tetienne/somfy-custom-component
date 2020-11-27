"""Support for Somfy Covers."""

import logging
from typing import List, Optional
from homeassistant.components.climate.const import (
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    PRESET_AWAY,
    PRESET_HOME,
    PRESET_SLEEP,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.helpers import temperature
from pymfy.api.devices.thermostat import DurationType, Thermostat, HvacState, TargetMode
from pymfy.api.devices.category import Category

from homeassistant.components.climate import ClimateEntity
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS

from . import SomfyEntity
from .const import API, COORDINATOR, DOMAIN

_LOGGER = logging.getLogger(__name__)

SUPPORTED_CATEGORIES = {Category.HVAC.value}

PRESETS_MAPPING = {
    TargetMode.AT_HOME: PRESET_HOME,
    TargetMode.AWAY: PRESET_AWAY,
    TargetMode.SLEEP: PRESET_SLEEP,
    TargetMode.MANUEL: "manual",
}
REVERSE_PRESET_MAPPING = {v: k for k, v in PRESETS_MAPPING.items()}

HVAC_MODES_MAPPING = {HvacState.COOL: HVAC_MODE_COOL, HvacState.HEAT: HVAC_MODE_HEAT}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Somfy cover platform."""

    def get_thermostats():
        """Retrieve thermostats."""
        domain_data = hass.data[DOMAIN]
        coordinator = domain_data[COORDINATOR]
        api = domain_data[API]

        return [
            SomfyClimate(coordinator, device_id, api)
            for device_id, device in coordinator.data.items()
            if SUPPORTED_CATEGORIES & set(device.categories)
        ]

    async_add_entities(await hass.async_add_executor_job(get_thermostats))


class SomfyClimate(SomfyEntity, ClimateEntity):
    """Representation of a Somfy thermostat device."""

    def __init__(self, coordinator, device_id, api):
        """Initialize the Somfy device."""
        super().__init__(coordinator, device_id, api)
        self.categories = set(self.device.categories)
        self.climate = None
        self._create_device()

    def _create_device(self):
        """Update the device with the latest data."""
        self.climate = Thermostat(self.device, self.api)

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        supported_features = SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE
        return supported_features

    @property
    def temperature_unit(self):
        """Return the unit of measurement used by the platform."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self.climate.get_ambient_temperature()

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self.climate.get_target_temperature()

    @property
    def current_humidity(self):
        """Return the current humidity."""
        return self.climate.get_humidity()

    @property
    def hvac_mode(self) -> str:
        """Return hvac operation ie. heat, cool mode."""
        mode = self.climate.get_hvac_state()
        return HVAC_MODES_MAPPING.get(mode)

    @property
    def hvac_modes(self) -> List[str]:
        """Return the list of available hvac operation modes."""
        return [HVAC_MODE_HEAT, HVAC_MODE_COOL]

    @property
    def hvac_action(self) -> str:
        """Return the current running hvac operation if supported."""
        if not self.current_temperature or not self.target_temperature:
            return CURRENT_HVAC_IDLE

        if (
            self.hvac_mode == HVAC_MODE_HEAT
            and self.current_temperature < self.target_temperature
        ):
            return CURRENT_HVAC_HEAT

        if (
            self.hvac_mode == HVAC_MODE_COOL
            and self.current_temperature > self.target_temperature
        ):
            return CURRENT_HVAC_HEAT

        return CURRENT_HVAC_IDLE

    @property
    def preset_mode(self) -> Optional[str]:
        """Return the current preset mode."""
        mode = self.climate.get_target_mode()
        return REVERSE_PRESET_MAPPING.get(mode)

    @property
    def preset_modes(self) -> Optional[List[str]]:
        """Return a list of available preset modes."""
        return list(PRESETS_MAPPING.values())

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if self.preset_mode == preset_mode:
            return

        if preset_mode == PRESET_HOME:
            temperature = self.climate.get_at_home_temperature()
        elif preset_mode == PRESET_AWAY:
            temperature = self.climate.get_away_temperature()
        elif preset_mode == PRESET_SLEEP:
            temperature = self.climate.get_night_temperature()
        else:
            _LOGGER.error("Preset mode not supported: %s", preset_mode)
            return

        self.climate.set_target(
            REVERSE_PRESET_MAPPING[preset_mode],
            temperature,
            DurationType.FURTHER_NOTICE,
        )
