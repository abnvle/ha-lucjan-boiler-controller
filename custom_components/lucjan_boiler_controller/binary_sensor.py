"""Binary sensor platform for Lucjan Boiler integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import LucjanCoordinator, LucjanData
from .entity import LucjanEntity


@dataclass(frozen=True, kw_only=True)
class LucjanBinarySensorDescription(BinarySensorEntityDescription):
    """Describe a Lucjan binary sensor."""

    value_fn: Callable[[LucjanData], bool]


BINARY_SENSOR_DESCRIPTIONS: tuple[LucjanBinarySensorDescription, ...] = (
    LucjanBinarySensorDescription(
        key="pump_co",
        name="Pompa CO",
        icon="mdi:pump",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda data: data.pump_co,
    ),
    LucjanBinarySensorDescription(
        key="pump_cwu1",
        name="Pompa CWU1",
        icon="mdi:pump",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda data: data.pump_cwu1,
    ),
    LucjanBinarySensorDescription(
        key="pump_cwu2",
        name="Pompa CWU2",
        icon="mdi:pump",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda data: data.pump_cwu2,
    ),
    LucjanBinarySensorDescription(
        key="circulation",
        name="Pompa cyrkulacyjna",
        icon="mdi:pump",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda data: data.circulation,
    ),
    LucjanBinarySensorDescription(
        key="feeder",
        name="Podajnik",
        icon="mdi:transfer-right",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda data: data.feeder,
    ),
    LucjanBinarySensorDescription(
        key="thermostat",
        name="Termostat",
        icon="mdi:thermostat",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda data: data.thermostat,
    ),
    LucjanBinarySensorDescription(
        key="alarm",
        name="Alarm",
        icon="mdi:alert-circle",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: data.alarm,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lucjan Boiler binary sensors."""
    coordinator: LucjanCoordinator = entry.runtime_data

    async_add_entities(
        LucjanBinarySensor(coordinator, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class LucjanBinarySensor(LucjanEntity, BinarySensorEntity):
    """Binary sensor for Lucjan Boiler."""

    entity_description: LucjanBinarySensorDescription

    def __init__(
        self,
        coordinator: LucjanCoordinator,
        description: LucjanBinarySensorDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_name = description.name

    @property
    def is_on(self) -> bool | None:
        """Return true if sensor is on."""
        if self.lucjan_data is None:
            return None
        return self.entity_description.value_fn(self.lucjan_data)
