"""Switch platform for Lucjan Boiler integration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from typing import Any, Callable, Coroutine

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import LucjanApi
from .coordinator import LucjanCoordinator, LucjanData
from .entity import LucjanEntity

_LOGGER = logging.getLogger(__name__)

COMMAND_DELAY = 3


@dataclass(frozen=True, kw_only=True)
class LucjanSwitchDescription(SwitchEntityDescription):
    """Describe a Lucjan switch."""

    is_on_fn: Callable[[LucjanData], bool]
    turn_on_fn: Callable[[LucjanApi], Coroutine]
    turn_off_fn: Callable[[LucjanApi], Coroutine]
    manual_only: bool = False


SWITCH_DESCRIPTIONS: tuple[LucjanSwitchDescription, ...] = (
    LucjanSwitchDescription(
        key="switch_auto_mode",
        name="Tryb AUTO",
        icon="mdi:auto-fix",
        is_on_fn=lambda data: data.boiler_mode == "AUTO",
        turn_on_fn=lambda api: api.async_set_boiler_mode(True),
        turn_off_fn=lambda api: api.async_set_boiler_mode(False),
    ),
    LucjanSwitchDescription(
        key="switch_pump_co",
        name="Pompa CO",
        icon="mdi:pump",
        is_on_fn=lambda data: data.pump_co,
        turn_on_fn=lambda api: api.async_set_pump_co(True),
        turn_off_fn=lambda api: api.async_set_pump_co(False),
        manual_only=True,
    ),
    LucjanSwitchDescription(
        key="switch_pump_cwu",
        name="Pompa CWU",
        icon="mdi:pump",
        is_on_fn=lambda data: data.pump_cwu1,
        turn_on_fn=lambda api: api.async_set_pump_cwu(True),
        turn_off_fn=lambda api: api.async_set_pump_cwu(False),
        manual_only=True,
    ),
    LucjanSwitchDescription(
        key="switch_pump_cwu2",
        name="Pompa CWU2",
        icon="mdi:pump",
        is_on_fn=lambda data: data.pump_cwu2,
        turn_on_fn=lambda api: api.async_set_pump_cwu2(True),
        turn_off_fn=lambda api: api.async_set_pump_cwu2(False),
        manual_only=True,
    ),
    LucjanSwitchDescription(
        key="switch_circulation",
        name="Pompa cyrkulacyjna",
        icon="mdi:pump",
        is_on_fn=lambda data: data.circulation,
        turn_on_fn=lambda api: api.async_set_pump_circulation(True),
        turn_off_fn=lambda api: api.async_set_pump_circulation(False),
        manual_only=True,
    ),
    LucjanSwitchDescription(
        key="switch_feeder",
        name="Podajnik",
        icon="mdi:transfer-right",
        is_on_fn=lambda data: data.feeder,
        turn_on_fn=lambda api: api.async_set_feeder(True),
        turn_off_fn=lambda api: api.async_set_feeder(False),
        manual_only=True,
    ),
    LucjanSwitchDescription(
        key="switch_cwu_priorytet",
        name="Priorytet CWU",
        icon="mdi:water-boiler-alert",
        is_on_fn=lambda data: data.cwu_priorytet == "WLACZ",
        turn_on_fn=lambda api: api.async_set_config_param(
            "CWU_PRIORYTET", "WLACZ"
        ),
        turn_off_fn=lambda api: api.async_set_config_param(
            "CWU_PRIORYTET", "WYLACZ"
        ),
    ),
    LucjanSwitchDescription(
        key="switch_co_zawor4d",
        name="Obwód CO + zawór 4D",
        icon="mdi:valve",
        is_on_fn=lambda data: data.co_mode == "ZIMA",
        turn_on_fn=lambda api: api.async_set_co_circuit(True),
        turn_off_fn=lambda api: api.async_set_co_circuit(False),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lucjan Boiler switches."""
    coordinator: LucjanCoordinator = entry.runtime_data

    async_add_entities(
        LucjanSwitch(coordinator, description)
        for description in SWITCH_DESCRIPTIONS
    )


class LucjanSwitch(LucjanEntity, SwitchEntity):
    """Switch entity for Lucjan Boiler control."""

    entity_description: LucjanSwitchDescription
    _attr_assumed_state = True

    def __init__(
        self,
        coordinator: LucjanCoordinator,
        description: LucjanSwitchDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_name = description.name
        self._optimistic_state: bool | None = None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not super().available:
            return False
        if (
            self.entity_description.manual_only
            and self.lucjan_data is not None
            and self.lucjan_data.boiler_mode == "AUTO"
        ):
            return False
        return True

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs: dict[str, Any] = {}
        if self.entity_description.manual_only:
            if (
                self.lucjan_data is not None
                and self.lucjan_data.boiler_mode == "AUTO"
            ):
                attrs["info"] = "Sterowanie wymaga trybu RĘCZNY"
            attrs["wymaga_trybu_recznego"] = True
        return attrs

    @property
    def is_on(self) -> bool | None:
        """Return true if switch is on."""
        if self._optimistic_state is not None:
            return self._optimistic_state
        if self.lucjan_data is None:
            return None
        return self.entity_description.is_on_fn(self.lucjan_data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        _LOGGER.debug("Turning on: %s", self.entity_description.key)
        self._optimistic_state = True
        self.async_write_ha_state()

        success = await self.entity_description.turn_on_fn(
            self.coordinator.api
        )
        if not success:
            _LOGGER.error("Failed to turn on %s", self.entity_description.key)
            self._optimistic_state = None
            self.async_write_ha_state()
            return

        await asyncio.sleep(COMMAND_DELAY)
        self._optimistic_state = None
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        _LOGGER.debug("Turning off: %s", self.entity_description.key)
        self._optimistic_state = False
        self.async_write_ha_state()

        success = await self.entity_description.turn_off_fn(
            self.coordinator.api
        )
        if not success:
            _LOGGER.error(
                "Failed to turn off %s", self.entity_description.key
            )
            self._optimistic_state = None
            self.async_write_ha_state()
            return

        await asyncio.sleep(COMMAND_DELAY)
        self._optimistic_state = None
        await self.coordinator.async_request_refresh()
