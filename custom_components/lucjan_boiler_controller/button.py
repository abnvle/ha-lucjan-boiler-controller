"""Button platform for Lucjan Boiler integration."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Callable, Coroutine

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import LucjanApi
from .coordinator import LucjanCoordinator
from .entity import LucjanEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class LucjanButtonDescription(ButtonEntityDescription):
    """Describe a Lucjan button."""

    press_fn: Callable[[LucjanApi], Coroutine]


BUTTON_DESCRIPTIONS: tuple[LucjanButtonDescription, ...] = (
    LucjanButtonDescription(
        key="alarm_reset",
        name="Reset alarmu",
        icon="mdi:alert-remove",
        press_fn=lambda api: api.async_alarm_reset(),
    ),
    LucjanButtonDescription(
        key="config_reload",
        name="Przeładuj konfigurację",
        icon="mdi:reload",
        press_fn=lambda api: api.async_config_reload(),
    ),
    LucjanButtonDescription(
        key="hopper_full",
        name="Zasobnik do pełna",
        icon="mdi:basket-fill",
        press_fn=lambda api: api.async_hopper_full(),
    ),
    LucjanButtonDescription(
        key="reset_controller",
        name="Reset sterownika",
        icon="mdi:restart",
        press_fn=lambda api: api.async_reset_controller(),
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lucjan Boiler buttons."""
    coordinator: LucjanCoordinator = entry.runtime_data

    async_add_entities(
        LucjanButton(coordinator, description)
        for description in BUTTON_DESCRIPTIONS
    )


class LucjanButton(LucjanEntity, ButtonEntity):
    """Button entity for Lucjan Boiler commands."""

    entity_description: LucjanButtonDescription

    def __init__(
        self,
        coordinator: LucjanCoordinator,
        description: LucjanButtonDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_name = description.name

    async def async_press(self) -> None:
        """Handle button press."""
        _LOGGER.debug("Button pressed: %s", self.entity_description.key)
        await self.entity_description.press_fn(self.coordinator.api)
        await self.coordinator.async_request_refresh()
