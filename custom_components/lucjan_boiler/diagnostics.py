"""Diagnostics support for Lucjan Boiler integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from .coordinator import LucjanCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: LucjanCoordinator = entry.runtime_data
    data = coordinator.data

    # Redact sensitive info
    config_data = dict(entry.data)
    config_data[CONF_PASSWORD] = "**REDACTED**"

    diagnostics: dict[str, Any] = {
        "config_entry": {
            "data": config_data,
            "options": dict(entry.options),
        },
    }

    if data:
        diagnostics["controller_data"] = {
            "raw_thermos": data.raw_thermos,
            "firmware_version": data.firmware_version,
            "uptime_seconds": data.uptime_seconds,
            "uptime_formatted": data.uptime_formatted,
            "temperatures": data.temperatures,
            "binary_states": {
                "pump_co": data.pump_co,
                "pump_cwu1": data.pump_cwu1,
                "pump_cwu2": data.pump_cwu2,
                "circulation": data.circulation,
                "feeder": data.feeder,
                "thermostat": data.thermostat,
                "alarm": data.alarm,
            },
            "fan": {
                "power": data.fan_power,
                "modulation": data.fan_modulation,
            },
            "hopper": {
                "level_percent": data.hopper_level_percent,
                "cm": data.hopper_cm,
                "feeder_time_s": data.feeder_time_s,
                "feeder_time_remaining_s": data.feeder_time_remaining_s,
                "feeder_time_total_s": data.feeder_time_total_s,
                "g_per_min": data.feeder_g_per_min,
                "fuel_consumption_kg": data.fuel_consumption_kg,
            },
            "config": {
                "target_co": data.target_temp_co,
                "target_cwu": data.target_temp_cwu,
                "boiler_mode": data.boiler_mode,
                "algorithm": data.algorithm,
                "co_mode": data.co_mode,
                "cwu_mode": data.cwu_mode,
                "co_algorytm": data.co_algorytm,
                "cwu_algorytm": data.cwu_algorytm,
                "cwu_priorytet": data.cwu_priorytet,
                "cwu_histereza": data.cwu_histereza_deg,
                "cwu_t_max": data.cwu_t_max,
                "piec_histereza": data.piec_histereza,
                "piec_t_max": data.piec_t_max,
                "piec_t_min": data.piec_t_min,
                "zawor4d_tryb": data.zawor4d_tryb,
                "zawor4d_zadana": data.zawor4d_zadana,
                "zawor4d_czujnik": data.zawor4d_czujnik,
                "zawor4d_histereza": data.zawor4d_histereza,
                "zawor4d_preset": data.zawor4d_preset,
                "cyrkulacja_algorytm": data.cyrkulacja_algorytm,
                "cyrkulacja_tmin": data.cyrkulacja_tmin,
                "autolato_temp": data.autolato_temp,
                "autolato_twew": data.autolato_twew,
                "autolato_histereza": data.autolato_histereza,
            },
        }

    return diagnostics
