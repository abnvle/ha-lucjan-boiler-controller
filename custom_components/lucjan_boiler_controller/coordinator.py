"""DataUpdateCoordinator for Lucjan Boiler integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import LucjanApi, LucjanApiError, LucjanConnectionError
from .const import DOMAIN, TEMP_SENSORS

_LOGGER = logging.getLogger(__name__)


class LucjanData:
    """Parsed data from Lucjan controller.

    Real thermos.json example:
    {"thermos":[{"t": 52.6},{"t": 38.0}, ...],"wen0": 41,"wen1": 41,
     "podcm": -1,"podcmp": -1,"podcz": 4165,"podczzas": 0,"podczdo": 41538,
     "podgmin": 260,"pod": 0,"co": 1,"cwu1": 0,"cwu2": 0,"cyrk": 0,
     "ter": 0,"al": 0,"time":83198,"ver":"0.1.0.130.35"}
    """

    def __init__(self, thermos: dict[str, Any], config: dict[str, str]) -> None:
        """Initialize with raw data."""
        self.raw_thermos = thermos
        self.raw_config = config

        # Parse temperatures from thermos array
        self.temperatures: dict[str, float | None] = {}
        thermos_list = thermos.get("thermos", [])
        for i, sensor_key in enumerate(TEMP_SENSORS):
            if i < len(thermos_list):
                val = thermos_list[i].get("t")
                self.temperatures[sensor_key] = _safe_float(val)
            else:
                self.temperatures[sensor_key] = None

        # Parse binary states (values are int 0/1)
        self.pump_co: bool = _int_to_bool(thermos.get("co"))
        self.pump_cwu1: bool = _int_to_bool(thermos.get("cwu1"))
        self.pump_cwu2: bool = _int_to_bool(thermos.get("cwu2"))
        self.circulation: bool = _int_to_bool(thermos.get("cyrk"))
        self.feeder: bool = _int_to_bool(thermos.get("pod"))
        self.thermostat: bool = _int_to_bool(thermos.get("ter"))
        self.alarm: bool = _int_to_bool(thermos.get("al"))

        # Fan data (percentage values)
        self.fan_power: float | None = _safe_float(thermos.get("wen0"))
        self.fan_modulation: float | None = _safe_float(thermos.get("wen1"))

        # Hopper/feeder data (-1 means sensor not available)
        self.feeder_time_s: float | None = _safe_float(thermos.get("podcz"))
        self.feeder_time_remaining_s: float | None = _safe_positive(
            thermos.get("podczzas")
        )
        self.feeder_time_total_s: float | None = _safe_positive(
            thermos.get("podczdo")
        )
        self.feeder_g_per_min: float | None = _safe_positive(
            thermos.get("podgmin")
        )
        self.hopper_cm: float | None = _safe_positive(thermos.get("podcm"))
        self.hopper_percent_raw: float | None = _safe_positive(
            thermos.get("podcmp")
        )

        # System info
        self.firmware_version: str = str(thermos.get("ver", "unknown"))
        self.uptime_seconds: int | None = _safe_int(thermos.get("time"))

        # Config-derived setpoints
        self.target_temp_co: float | None = _safe_float(
            config.get("PIEC_ZADANA")
        )
        self.target_temp_cwu: float | None = _safe_float(
            config.get("CWU_ZADANA")
        )
        self.boiler_mode: str = config.get("PIEC_TRYB", "unknown")
        self.co_mode: str = config.get("CO_TRYB", "unknown")
        self.cwu_mode: str = config.get("CWU_TRYB", "unknown")
        self.algorithm: str = config.get("PIEC_ALGORYTM", "unknown")
        self.piec_t_max: float | None = _safe_float(config.get("PIEC_T_MAX"))
        self.piec_t_min: float | None = _safe_float(config.get("PIEC_T_MIN"))

        # Additional config parameters for control/display
        self.co_algorytm: str = config.get("CO_ALGORYTM", "unknown")
        self.cwu_algorytm: str = config.get("CWU_ALGORYTM", "unknown")
        self.cwu_priorytet: str = config.get("CWU_PRIORYTET", "unknown")
        self.cwu_histereza: float | None = _safe_float(
            config.get("CWU_HISTEREZA")
        )
        self.cwu_t_max: float | None = _safe_float(config.get("CWU_T_MAX"))
        self.piec_histereza_raw: float | None = _safe_float(
            config.get("PIEC_HISTEREZA")
        )

        # Zawór 4D
        self.zawor4d_tryb: str = config.get("ZAWOR4D-TRYB", "unknown")
        self.zawor4d_zadana: float | None = _safe_float(
            config.get("ZAWOR4D-ZADANA")
        )
        self.zawor4d_czujnik: str = config.get("ZAWOR4D-CZUJNIK", "unknown")
        self.zawor4d_histereza_raw: float | None = _safe_float(
            config.get("ZAWOR4D-HISTEREZA")
        )
        self.zawor4d_preset: float | None = _safe_float(
            config.get("ZAWOR4D-PRESET")
        )

        # Cyrkulacja
        self.cyrkulacja_algorytm: str = config.get(
            "CYRKULACJA_ALGORYTM", "unknown"
        )
        self.cyrkulacja_tmin: float | None = _safe_float(
            config.get("CYRKULACJA_TMIN")
        )

        # Auto-lato
        self.autolato_temp: float | None = _safe_float(
            config.get("AUTOLATO_TEMP")
        )
        self.autolato_twew: float | None = _safe_float(
            config.get("AUTOLATO_TWEW")
        )
        self.autolato_histereza_raw: float | None = _safe_float(
            config.get("AUTOLATO_HISTEREZA")
        )

    @property
    def hopper_level_percent(self) -> float | None:
        """Calculate hopper level as percentage."""
        if self.hopper_percent_raw is not None:
            return self.hopper_percent_raw
        if (
            self.feeder_time_remaining_s is not None
            and self.feeder_time_total_s is not None
            and self.feeder_time_total_s > 0
        ):
            return round(
                (self.feeder_time_remaining_s / self.feeder_time_total_s) * 100,
                1,
            )
        return None

    @property
    def fuel_consumption_kg(self) -> float | None:
        """Calculate total fuel consumption in kg since boot."""
        if (
            self.feeder_time_s is not None
            and self.feeder_g_per_min is not None
            and self.feeder_g_per_min > 0
        ):
            return round(
                self.feeder_time_s / 60 * self.feeder_g_per_min / 1000, 2
            )
        return None

    @property
    def uptime_formatted(self) -> str | None:
        """Return uptime as human-readable string."""
        if self.uptime_seconds is None:
            return None
        s = self.uptime_seconds
        h = s // 3600
        m = (s % 3600) // 60
        return f"{h}h {m}m"

    @property
    def piec_histereza(self) -> float | None:
        """Return boiler hysteresis in degrees (config stores *10)."""
        if self.piec_histereza_raw is not None:
            return self.piec_histereza_raw / 10
        return None

    @property
    def cwu_histereza_deg(self) -> float | None:
        """Return CWU hysteresis in degrees."""
        return self.cwu_histereza

    @property
    def zawor4d_histereza(self) -> float | None:
        """Return 4D valve hysteresis in degrees (config stores *10)."""
        if self.zawor4d_histereza_raw is not None:
            return self.zawor4d_histereza_raw / 10
        return None

    @property
    def autolato_histereza(self) -> float | None:
        """Return auto-summer hysteresis in degrees (config stores *10)."""
        if self.autolato_histereza_raw is not None:
            return self.autolato_histereza_raw / 10
        return None


class LucjanCoordinator(DataUpdateCoordinator[LucjanData]):
    """Coordinator to manage fetching data from Lucjan controller."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: LucjanApi,
        scan_interval: int,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.api = api

    async def _async_update_data(self) -> LucjanData:
        """Fetch data from the controller."""
        try:
            thermos = await self.api.async_get_thermos()

            # Try to get config for setpoints, but don't fail if unavailable
            config: dict[str, str] = {}
            try:
                config = await self.api.async_get_config()
            except LucjanApiError:
                _LOGGER.debug("Could not fetch config.txt, using defaults")

            return LucjanData(thermos=thermos, config=config)

        except LucjanConnectionError as err:
            raise UpdateFailed(f"Connection error: {err}") from err
        except LucjanApiError as err:
            raise UpdateFailed(f"API error: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err


def _safe_float(value: Any) -> float | None:
    """Safely convert a value to float."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _safe_positive(value: Any) -> float | None:
    """Safely convert to float, returning None for negative values (-1 = no sensor)."""
    result = _safe_float(value)
    if result is not None and result < 0:
        return None
    return result


def _safe_int(value: Any) -> int | None:
    """Safely convert a value to int."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _int_to_bool(value: Any) -> bool:
    """Convert int 0/1 to bool."""
    if value is None:
        return False
    try:
        return int(value) != 0
    except (ValueError, TypeError):
        return False
