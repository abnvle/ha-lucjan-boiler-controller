"""Base entity for Lucjan Boiler integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import LucjanCoordinator, LucjanData


class LucjanEntity(CoordinatorEntity[LucjanCoordinator]):
    """Base entity for Lucjan Boiler."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LucjanCoordinator,
        key: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{coordinator.api.host}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        data = self.coordinator.data
        fw = data.firmware_version if data else "unknown"
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.api.host)},
            name=f"Lucjan ({self.coordinator.api.host})",
            manufacturer=MANUFACTURER,
            model="Sterownik Pieca CO",
            sw_version=fw,
            configuration_url=f"http://{self.coordinator.api.host}",
        )

    @property
    def lucjan_data(self) -> LucjanData | None:
        """Return the current data."""
        return self.coordinator.data
