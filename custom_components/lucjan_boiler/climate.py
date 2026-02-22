"""Climate platform for Lucjan Boiler integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import LucjanCoordinator
from .entity import LucjanEntity

_LOGGER = logging.getLogger(__name__)

COMMAND_DELAY = 3


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lucjan Boiler climate entities."""
    coordinator: LucjanCoordinator = entry.runtime_data

    entities: list[ClimateEntity] = [
        LucjanBoilerClimate(coordinator),
        LucjanCWUClimate(coordinator),
    ]

    async_add_entities(entities)


class LucjanBoilerClimate(LucjanEntity, ClimateEntity):
    """Climate entity for the CO boiler."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_target_temperature_step = 1.0
    _attr_min_temp = 30
    _attr_max_temp = 80
    _attr_icon = "mdi:radiator"

    def __init__(self, coordinator: LucjanCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator, "climate_co")
        self._attr_name = "Piec CO"

    @property
    def current_temperature(self) -> float | None:
        """Return the current boiler temperature (tPIEC)."""
        if self.lucjan_data is None:
            return None
        return self.lucjan_data.temperatures.get("tPIEC")

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        if self.lucjan_data is None:
            return None
        return self.lucjan_data.target_temp_co

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        if self.lucjan_data is None:
            return HVACMode.OFF
        return HVACMode.HEAT

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current HVAC action."""
        if self.lucjan_data is None:
            return None
        if self.lucjan_data.fan_power and self.lucjan_data.fan_power > 0:
            return HVACAction.HEATING
        if self.lucjan_data.feeder:
            return HVACAction.HEATING
        return HVACAction.IDLE

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs: dict[str, Any] = {}
        if self.lucjan_data:
            attrs["algorytm"] = self.lucjan_data.algorithm
            attrs["tryb"] = self.lucjan_data.boiler_mode
            attrs["tryb_co"] = self.lucjan_data.co_mode
            if self.lucjan_data.piec_t_max is not None:
                attrs["t_max"] = self.lucjan_data.piec_t_max
            if self.lucjan_data.piec_t_min is not None:
                attrs["t_min_pompa"] = self.lucjan_data.piec_t_min
            if self.lucjan_data.piec_histereza is not None:
                attrs["histereza"] = self.lucjan_data.piec_histereza
            temp_powrot = self.lucjan_data.temperatures.get("tPOWROT")
            if temp_powrot is not None:
                attrs["temperatura_powrotu"] = temp_powrot
            temp_spaliny = self.lucjan_data.temperatures.get("tSPALINY")
            if temp_spaliny is not None:
                attrs["temperatura_spalin"] = temp_spaliny
            attrs["co_algorytm"] = self.lucjan_data.co_algorytm
        return attrs

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the target temperature.

        Uses /set for immediate runtime change + config.txt upload
        so the coordinator reads the updated value on next poll.
        """
        temp = kwargs.get("temperature")
        if temp is not None:
            temp_int = int(round(temp))
            _LOGGER.debug("Setting CO target temperature to %s", temp_int)
            # Immediate runtime change
            await self.coordinator.api.async_set_piec_zadana(temp_int)
            # Persist to config.txt so coordinator reads it back
            await self.coordinator.api.async_set_config_param(
                "PIEC_ZADANA", str(temp_int)
            )
            await asyncio.sleep(COMMAND_DELAY)
            await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode (informational only)."""
        _LOGGER.debug("HVAC mode set to %s (boiler always heats)", hvac_mode)


class LucjanCWUClimate(LucjanEntity, ClimateEntity):
    """Climate entity for CWU (hot water)."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_target_temperature_step = 1.0
    _attr_min_temp = 30
    _attr_max_temp = 65
    _attr_icon = "mdi:water-boiler"

    def __init__(self, coordinator: LucjanCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator, "climate_cwu")
        self._attr_name = "CWU"

    @property
    def current_temperature(self) -> float | None:
        """Return current CWU temperature."""
        if self.lucjan_data is None:
            return None
        return self.lucjan_data.temperatures.get("tCWU")

    @property
    def target_temperature(self) -> float | None:
        """Return the target CWU temperature."""
        if self.lucjan_data is None:
            return None
        return self.lucjan_data.target_temp_cwu

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        if self.lucjan_data is None:
            return HVACMode.OFF
        if self.lucjan_data.cwu_mode in ("WYLACZ", "unknown"):
            return HVACMode.OFF
        return HVACMode.HEAT

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current HVAC action."""
        if self.lucjan_data is None:
            return None
        if self.lucjan_data.pump_cwu1:
            return HVACAction.HEATING
        return HVACAction.IDLE

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs: dict[str, Any] = {}
        if self.lucjan_data:
            attrs["tryb_cwu"] = self.lucjan_data.cwu_mode
            attrs["cwu_algorytm"] = self.lucjan_data.cwu_algorytm
            if self.lucjan_data.cwu_histereza_deg is not None:
                attrs["histereza"] = self.lucjan_data.cwu_histereza_deg
            if self.lucjan_data.cwu_t_max is not None:
                attrs["t_max"] = self.lucjan_data.cwu_t_max
            attrs["priorytet"] = self.lucjan_data.cwu_priorytet
        return attrs

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the target CWU temperature.

        Uses /set for immediate runtime change + config.txt upload
        so the coordinator reads the updated value on next poll.
        """
        temp = kwargs.get("temperature")
        if temp is not None:
            temp_int = int(round(temp))
            _LOGGER.debug("Setting CWU target temperature to %s", temp_int)
            await self.coordinator.api.async_set_cwu_zadana(temp_int)
            await self.coordinator.api.async_set_config_param(
                "CWU_ZADANA", str(temp_int)
            )
            await asyncio.sleep(COMMAND_DELAY)
            await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode."""
        _LOGGER.debug("CWU HVAC mode set to %s", hvac_mode)
