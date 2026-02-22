"""API client for Lucjan Boiler controller."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import DEFAULT_PORT, ENDPOINT_CONFIG, ENDPOINT_THERMOS

_LOGGER = logging.getLogger(__name__)

TIMEOUT = aiohttp.ClientTimeout(total=10)


class LucjanApiError(Exception):
    """Base exception for Lucjan API errors."""


class LucjanConnectionError(LucjanApiError):
    """Connection error."""


class LucjanAuthError(LucjanApiError):
    """Authentication error."""


class LucjanApi:
    """API client for Lucjan Boiler controller."""

    def __init__(
        self,
        host: str,
        username: str = "admin",
        password: str = "admin",
        session: aiohttp.ClientSession | None = None,
        port: int = DEFAULT_PORT,
    ) -> None:
        """Initialize the API client."""
        self._host = host
        self._session = session
        self._base_url = (
            f"http://{host}:{port}" if port != 80 else f"http://{host}"
        )
        self._auth = (
            aiohttp.BasicAuth(username, password) if username else None
        )

    @property
    def host(self) -> str:
        """Return the host."""
        return self._host

    # ── HTTP helpers ──

    async def _get(self, endpoint: str) -> aiohttp.ClientResponse:
        """Make a GET request."""
        url = f"{self._base_url}{endpoint}"
        _LOGGER.debug("GET %s", url)

        if self._session is None:
            raise LucjanConnectionError("No HTTP session available")

        try:
            response = await self._session.get(
                url, auth=self._auth, timeout=TIMEOUT,
            )
            if response.status == 401:
                raise LucjanAuthError("Invalid credentials")
            if response.status != 200:
                raise LucjanApiError(f"HTTP {response.status} from {url}")
            return response

        except asyncio.TimeoutError as err:
            raise LucjanConnectionError(
                f"Timeout connecting to {self._host}"
            ) from err
        except aiohttp.ClientError as err:
            raise LucjanConnectionError(
                f"Error connecting to {self._host}: {err}"
            ) from err

    async def _put(self, endpoint: str, data: bytes) -> aiohttp.ClientResponse:
        """Make a PUT request with binary data."""
        url = f"{self._base_url}{endpoint}"
        _LOGGER.debug("PUT %s (%d bytes)", url, len(data))

        if self._session is None:
            raise LucjanConnectionError("No HTTP session available")

        try:
            response = await self._session.put(
                url, auth=self._auth, timeout=TIMEOUT, data=data,
            )
            if response.status == 401:
                raise LucjanAuthError("Invalid credentials")
            if response.status != 200:
                raise LucjanApiError(f"HTTP {response.status} from {url}")
            return response

        except asyncio.TimeoutError as err:
            raise LucjanConnectionError(
                f"Timeout connecting to {self._host}"
            ) from err
        except aiohttp.ClientError as err:
            raise LucjanConnectionError(
                f"Error connecting to {self._host}: {err}"
            ) from err

    # ── Read endpoints ──

    async def async_get_thermos(self) -> dict[str, Any]:
        """Fetch thermos.json - main status data."""
        response = await self._get(ENDPOINT_THERMOS)
        data = await response.json(content_type=None)
        _LOGGER.debug("Thermos data: %s", data)
        return data

    async def async_get_config(self) -> dict[str, str]:
        """Fetch and parse config.txt."""
        response = await self._get(ENDPOINT_CONFIG)
        text = await response.text()
        return self._parse_config(text)

    async def async_get_config_raw(self) -> str:
        """Fetch raw config.txt content."""
        response = await self._get(ENDPOINT_CONFIG)
        return await response.text()

    async def async_test_connection(self) -> dict[str, Any]:
        """Test the connection and return thermos data."""
        return await self.async_get_thermos()

    # ── Runtime control via /setVARIABLE=VALUE ──

    async def async_set_variable(self, name: str, value: Any) -> bool:
        """Set a runtime variable via /setNAME=VALUE."""
        try:
            await self._get(f"/set{name}={value}")
            _LOGGER.debug("Set %s=%s OK", name, value)
            return True
        except LucjanApiError as err:
            _LOGGER.error("Failed to set %s=%s: %s", name, value, err)
            return False

    async def async_set_piec_zadana(self, temp: int) -> bool:
        """Set CO target temperature (runtime)."""
        return await self.async_set_variable("PIEC_ZADANA", temp)

    async def async_set_cwu_zadana(self, temp: int) -> bool:
        """Set CWU target temperature (runtime)."""
        return await self.async_set_variable("CWU_ZADANA", temp)

    async def async_set_pump_co(self, state: bool) -> bool:
        """Set CO pump on/off (RECZNY mode only)."""
        return await self.async_set_variable("OUT_POMPACO", 1 if state else 0)

    async def async_set_pump_cwu(self, state: bool) -> bool:
        """Set CWU pump on/off (RECZNY mode only)."""
        return await self.async_set_variable("OUT_POMPACWU", 1 if state else 0)

    async def async_set_pump_cwu2(self, state: bool) -> bool:
        """Set CWU2 pump on/off (RECZNY mode only)."""
        return await self.async_set_variable(
            "OUT_POMPACWU2", 1 if state else 0
        )

    async def async_set_pump_circulation(self, state: bool) -> bool:
        """Set circulation pump on/off (RECZNY mode only)."""
        return await self.async_set_variable(
            "OUT_POMPACYRK", 1 if state else 0
        )

    async def async_set_feeder(self, state: bool) -> bool:
        """Set feeder on/off (RECZNY mode only)."""
        return await self.async_set_variable(
            "OUT_PODAJNIK", 1 if state else 0
        )

    async def async_set_fan_power(self, value: int) -> bool:
        """Set fan power 0-100% (RECZNY mode only)."""
        return await self.async_set_variable("OUT_WENTYLATOR", int(value))

    # ── Config file control via /upload/config.txt + /configreload ──

    async def async_set_config_param(
        self, param: str, value: str
    ) -> bool:
        """Change a parameter in config.txt via upload + reload.

        This is the only way to change config parameters like PIEC_TRYB.
        Sequence: GET config.txt → modify → PUT upload/config.txt → configreload
        """
        try:
            raw_config = await self.async_get_config_raw()

            new_config = self._replace_config_param(raw_config, param, value)
            if new_config is None:
                _LOGGER.error(
                    "Parameter %s not found in config.txt", param
                )
                return False

            await self._put(
                "/upload/config.txt", new_config.encode("utf-8")
            )
            _LOGGER.debug("Uploaded modified config.txt")

            await asyncio.sleep(0.5)
            await self._get("/configreload")
            _LOGGER.debug("Config reloaded, %s=%s", param, value)
            return True

        except LucjanApiError as err:
            _LOGGER.error(
                "Failed to set config param %s=%s: %s", param, value, err
            )
            return False

    async def async_set_boiler_mode(self, auto: bool) -> bool:
        """Set boiler mode to AUTO or RECZNY via config upload."""
        mode = "AUTO" if auto else "RECZNY"
        return await self.async_set_config_param("PIEC_TRYB", mode)

    async def async_set_co_circuit(self, enabled: bool) -> bool:
        """Enable/disable CO circuit + 4D valve via config upload.

        ON = CO_TRYB = ZIMA (normal operation)
        OFF = CO_TRYB = ZIM (unrecognized value disables CO + closes 4D valve)
        """
        value = "ZIMA" if enabled else "ZIM"
        return await self.async_set_config_param("CO_TRYB", value)

    async def async_set_co_circuit(self, enabled: bool) -> bool:
        """Enable/disable CO circuit + 4D valve.

        Sequence required by the controller:
        1. Switch to RECZNY mode
        2. Set CO_TRYB = ZIMA or ZIM
        3. Switch back to AUTO mode

        ZIM is an unrecognized value that forces the controller
        to disable the CO pump and close the 4D valve.
        """
        co_value = "ZIMA" if enabled else "ZIM"
        try:
            # Step 1: Switch to RECZNY
            _LOGGER.debug("CO circuit: switching to RECZNY")
            await self.async_set_config_param("PIEC_TRYB", "RECZNY")
            await asyncio.sleep(1)

            # Step 2: Change CO_TRYB
            _LOGGER.debug("CO circuit: setting CO_TRYB=%s", co_value)
            await self.async_set_config_param("CO_TRYB", co_value)
            await asyncio.sleep(1)

            # Step 3: Switch back to AUTO
            _LOGGER.debug("CO circuit: switching back to AUTO")
            await self.async_set_config_param("PIEC_TRYB", "AUTO")

            _LOGGER.info("CO circuit set to %s", co_value)
            return True

        except LucjanApiError as err:
            _LOGGER.error("Failed to set CO circuit: %s", err)
            # Try to restore AUTO mode
            try:
                await self.async_set_config_param("PIEC_TRYB", "AUTO")
            except LucjanApiError:
                _LOGGER.error("Failed to restore AUTO mode!")
            return False

    # ── System commands ──

    async def async_alarm_reset(self) -> bool:
        """Reset alarm on the controller."""
        try:
            await self._get("/alarmreset")
            return True
        except LucjanApiError as err:
            _LOGGER.error("Failed to reset alarm: %s", err)
            return False

    async def async_config_reload(self) -> bool:
        """Reload configuration."""
        try:
            await self._get("/configreload")
            return True
        except LucjanApiError as err:
            _LOGGER.error("Failed to reload config: %s", err)
            return False

    async def async_hopper_full(self) -> bool:
        """Set hopper as full."""
        try:
            await self._get("/zasobnikfull")
            return True
        except LucjanApiError as err:
            _LOGGER.error("Failed to set hopper full: %s", err)
            return False

    async def async_reset_controller(self) -> bool:
        """Reset the controller."""
        try:
            await self._get("/reset")
            return True
        except LucjanApiError as err:
            _LOGGER.error("Failed to reset controller: %s", err)
            return False

    # ── Helpers ──

    @staticmethod
    def _replace_config_param(
        config_text: str, param: str, new_value: str
    ) -> str | None:
        """Replace a parameter value in config.txt content.

        Handles formats like:
          PARAM = VALUE
          PARAM=VALUE
          PARAM =VALUE
        Returns modified text or None if param not found.
        """
        lines = config_text.splitlines()
        found = False

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "=" in stripped:
                key, _, _ = stripped.partition("=")
                if key.strip() == param:
                    # Preserve original spacing style
                    if " = " in line:
                        lines[i] = f"{param} = {new_value}"
                    else:
                        lines[i] = f"{param}={new_value}"
                    found = True
                    break

        if not found:
            return None

        return "\n".join(lines) + "\n"

    @staticmethod
    def _parse_config(text: str) -> dict[str, str]:
        """Parse config.txt content into a dictionary."""
        config = {}
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                # Strip inline comments
                if "#" in value:
                    value = value[:value.index("#")].strip()
                if key and not key.startswith("#"):
                    config[key] = value
        return config
