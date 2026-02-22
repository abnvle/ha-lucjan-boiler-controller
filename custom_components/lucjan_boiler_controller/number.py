"""Number platform for Lucjan Boiler integration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from typing import Any, Callable

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import LucjanCoordinator, LucjanData
from .entity import LucjanEntity

_LOGGER = logging.getLogger(__name__)

COMMAND_DELAY = 3


@dataclass(frozen=True, kw_only=True)
class LucjanNumberDescription(NumberEntityDescription):
    """Describe a Lucjan number entity."""

    value_fn: Callable[[LucjanData], float | None]
    config_param: str | None = None
    runtime_param: str | None = None
    manual_only: bool = False


NUMBER_DESCRIPTIONS: tuple[LucjanNumberDescription, ...] = (
    # Runtime control (RECZNY mode only)
    LucjanNumberDescription(
        key="fan_power_control",
        name="Moc wentylatora",
        icon="mdi:fan",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.fan_power,
        runtime_param="OUT_WENTYLATOR",
        manual_only=True,
    ),
    # Config parameters (via config.txt upload)
    LucjanNumberDescription(
        key="zawor4d_zadana",
        name="Zawór 4D — temperatura zadana",
        icon="mdi:valve",
        native_min_value=25,
        native_max_value=60,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.zawor4d_zadana,
        config_param="ZAWOR4D-ZADANA",
    ),
    LucjanNumberDescription(
        key="autolato_temp",
        name="Auto-lato — próg temp. zewnętrznej",
        icon="mdi:sun-thermometer",
        native_min_value=5,
        native_max_value=25,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.autolato_temp,
        config_param="AUTOLATO_TEMP",
    ),
    LucjanNumberDescription(
        key="autolato_twew",
        name="Auto-lato — próg temp. wewnętrznej",
        icon="mdi:home-thermometer",
        native_min_value=18,
        native_max_value=30,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.autolato_twew,
        config_param="AUTOLATO_TWEW",
    ),
    LucjanNumberDescription(
        key="piec_t_max",
        name="Piec — temperatura maksymalna",
        icon="mdi:thermometer-alert",
        native_min_value=60,
        native_max_value=95,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.piec_t_max,
        config_param="PIEC_T_MAX",
    ),
    LucjanNumberDescription(
        key="piec_t_min",
        name="Piec — temp. załączenia pomp",
        icon="mdi:thermometer-low",
        native_min_value=30,
        native_max_value=55,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.piec_t_min,
        config_param="PIEC_T_MIN",
    ),
    LucjanNumberDescription(
        key="cyrkulacja_tmin",
        name="Cyrkulacja — min. temp. CWU",
        icon="mdi:thermometer-water",
        native_min_value=20,
        native_max_value=60,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.cyrkulacja_tmin,
        config_param="CYRKULACJA_TMIN",
    ),
    LucjanNumberDescription(
        key="cwu_t_max",
        name="CWU — temperatura maksymalna",
        icon="mdi:thermometer-alert",
        native_min_value=40,
        native_max_value=95,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.cwu_t_max,
        config_param="CWU_T_MAX",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lucjan Boiler number entities."""
    coordinator: LucjanCoordinator = entry.runtime_data

    async_add_entities(
        LucjanNumber(coordinator, description)
        for description in NUMBER_DESCRIPTIONS
    )


class LucjanNumber(LucjanEntity, NumberEntity):
    """Number entity for Lucjan Boiler parameters."""

    entity_description: LucjanNumberDescription

    def __init__(
        self,
        coordinator: LucjanCoordinator,
        description: LucjanNumberDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_name = description.name
        self._attr_native_min_value = description.native_min_value
        self._attr_native_max_value = description.native_max_value
        self._attr_native_step = description.native_step
        self._attr_native_unit_of_measurement = (
            description.native_unit_of_measurement
        )
        self._attr_mode = description.mode

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
            attrs["wymaga_trybu_recznego"] = True
            if (
                self.lucjan_data is not None
                and self.lucjan_data.boiler_mode == "AUTO"
            ):
                attrs["info"] = "Sterowanie wymaga trybu RĘCZNY"
        if self.entity_description.config_param:
            attrs["parametr_config"] = self.entity_description.config_param
        return attrs

    @property
    def native_value(self) -> float | None:
        """Return current value."""
        if self.lucjan_data is None:
            return None
        return self.entity_description.value_fn(self.lucjan_data)

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        int_value = int(round(value))
        desc = self.entity_description

        if desc.runtime_param:
            _LOGGER.debug("Setting runtime %s=%s", desc.runtime_param, int_value)
            await self.coordinator.api.async_set_variable(
                desc.runtime_param, int_value
            )
        elif desc.config_param:
            _LOGGER.debug("Setting config %s=%s", desc.config_param, int_value)
            await self.coordinator.api.async_set_config_param(
                desc.config_param, str(int_value)
            )

        await asyncio.sleep(COMMAND_DELAY)
        await self.coordinator.async_request_refresh()
