"""Select platform for Lucjan Boiler integration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from typing import Callable

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import LucjanCoordinator, LucjanData
from .entity import LucjanEntity

_LOGGER = logging.getLogger(__name__)

COMMAND_DELAY = 3


@dataclass(frozen=True, kw_only=True)
class LucjanSelectDescription(SelectEntityDescription):
    """Describe a Lucjan select entity."""

    options_list: list[str]
    current_fn: Callable[[LucjanData], str]
    config_param: str


SELECT_DESCRIPTIONS: tuple[LucjanSelectDescription, ...] = (
    LucjanSelectDescription(
        key="select_co_tryb",
        name="Tryb CO",
        icon="mdi:radiator",
        options_list=["ZIMA", "LATO", "ECOAL", "BRULI"],
        current_fn=lambda data: data.co_mode,
        config_param="CO_TRYB",
    ),
    LucjanSelectDescription(
        key="select_cwu_tryb",
        name="Tryb CWU",
        icon="mdi:water-boiler",
        options_list=["WLACZ", "WYLACZ", "BRULI", "ECOAL", "MIESZANIE"],
        current_fn=lambda data: data.cwu_mode,
        config_param="CWU_TRYB",
    ),
    LucjanSelectDescription(
        key="select_piec_algorytm",
        name="Algorytm palnika",
        icon="mdi:fire-circle",
        options_list=["RRM", "RRM2", "RR", "ECOAL", "ZASYPOWY", "WYLACZONY"],
        current_fn=lambda data: data.algorithm,
        config_param="PIEC_ALGORYTM",
    ),
    LucjanSelectDescription(
        key="select_zawor4d_tryb",
        name="Tryb zaworu 4D",
        icon="mdi:valve",
        options_list=["ZADANA", "KRZYWA", "WYLACZONY"],
        current_fn=lambda data: data.zawor4d_tryb,
        config_param="ZAWOR4D-TRYB",
    ),
    LucjanSelectDescription(
        key="select_cyrkulacja",
        name="Cyrkulacja CWU",
        icon="mdi:rotate-3d-variant",
        options_list=["CIAGLY", "CYKLICZNY", "WYLACZONY"],
        current_fn=lambda data: data.cyrkulacja_algorytm,
        config_param="CYRKULACJA_ALGORYTM",
    ),
    LucjanSelectDescription(
        key="select_co_algorytm",
        name="Algorytm pompy CO",
        icon="mdi:pump",
        options_list=["CIAGLY", "CYKLICZNY"],
        current_fn=lambda data: data.co_algorytm,
        config_param="CO_ALGORYTM",
    ),
    LucjanSelectDescription(
        key="select_cwu_algorytm",
        name="Algorytm pompy CWU",
        icon="mdi:pump",
        options_list=["CIAGLY", "CYKLICZNY"],
        current_fn=lambda data: data.cwu_algorytm,
        config_param="CWU_ALGORYTM",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lucjan Boiler select entities."""
    coordinator: LucjanCoordinator = entry.runtime_data

    async_add_entities(
        LucjanSelect(coordinator, description)
        for description in SELECT_DESCRIPTIONS
    )


class LucjanSelect(LucjanEntity, SelectEntity):
    """Select entity for Lucjan Boiler config parameters."""

    entity_description: LucjanSelectDescription

    def __init__(
        self,
        coordinator: LucjanCoordinator,
        description: LucjanSelectDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_name = description.name
        self._attr_options = description.options_list
        self._optimistic_value: str | None = None

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        if self._optimistic_value is not None:
            return self._optimistic_value
        if self.lucjan_data is None:
            return None
        value = self.entity_description.current_fn(self.lucjan_data)
        # Return value if it's in options, otherwise return as-is
        if value in self._attr_options:
            return value
        if value != "unknown":
            return value
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option via config.txt upload."""
        _LOGGER.debug(
            "Setting %s=%s", self.entity_description.config_param, option
        )
        self._optimistic_value = option
        self.async_write_ha_state()

        success = await self.coordinator.api.async_set_config_param(
            self.entity_description.config_param, option
        )

        if not success:
            _LOGGER.error(
                "Failed to set %s=%s",
                self.entity_description.config_param,
                option,
            )
            self._optimistic_value = None
            self.async_write_ha_state()
            return

        await asyncio.sleep(COMMAND_DELAY)
        self._optimistic_value = None
        await self.coordinator.async_request_refresh()
