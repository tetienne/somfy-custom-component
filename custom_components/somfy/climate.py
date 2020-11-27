"""Support for Somfy Covers."""

from typing import List
from homeassistant.components.climate.const import (
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    HVAC_MODE_HEAT_COOL,
    SUPPORT_TARGET_TEMPERATURE,
)
from pymfy.api.devices.thermostat import Thermostat, HvacState
from pymfy.api.devices.category import Category

from homeassistant.components.climate import ClimateEntity
from homeassistant.const import TEMP_CELSIUS

from . import SomfyEntity
from .const import API, COORDINATOR, DOMAIN

SUPPORTED_CATEGORIES = {Category.HVAC.value}


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
        supported_features = SUPPORT_TARGET_TEMPERATURE
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
    def current_humidity(self):
        """Return the current humidity."""
        return self.climate.get_humidity()

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self.climate.get_target_temperature()

    @property
    def hvac_mode(self) -> str:
        """Return hvac operation ie. heat, cool mode."""
        mode = self.climate.get_hvac_state()
        return {HvacState.COOL: HVAC_MODE_COOL, HvacState.HEAT: HVAC_MODE_HEAT}.get(
            mode
        )

    @property
    def hvac_modes(self) -> List[str]:
        """Return the list of available hvac operation modes."""
        return [HVAC_MODE_AUTO, HVAC_MODE_HEAT, HVAC_MODE_COOL]
