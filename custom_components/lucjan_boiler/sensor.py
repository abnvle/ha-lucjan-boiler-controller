"""Sensor platform for Lucjan Boiler integration."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfMass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from typing import Callable

from .const import DOMAIN, TEMP_SENSOR_NAMES, TEMP_SENSORS
from .coordinator import LucjanCoordinator
from .entity import LucjanEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lucjan Boiler sensors."""
    coordinator: LucjanCoordinator = entry.runtime_data

    entities: list[SensorEntity] = []

    # Temperature sensors (16x)
    for sensor_key in TEMP_SENSORS:
        entities.append(
            LucjanTemperatureSensor(coordinator, sensor_key)
        )

    # Fan power
    entities.append(LucjanFanPowerSensor(coordinator, "wen0", "Wentylator"))
    entities.append(
        LucjanFanPowerSensor(coordinator, "wen1", "Wentylator modulacja")
    )

    # Hopper / feeder stats
    entities.append(LucjanFuelConsumptionSensor(coordinator))
    entities.append(LucjanFeederTimeSensor(coordinator))
    entities.append(LucjanHopperLevelSensor(coordinator))

    # System
    entities.append(LucjanUptimeSensor(coordinator))
    entities.append(LucjanFirmwareSensor(coordinator))
    entities.append(LucjanAlgorithmSensor(coordinator))
    entities.append(LucjanBoilerModeSensor(coordinator))

    # Setpoints as sensors (read-only view)
    entities.append(LucjanSetpointSensor(coordinator, "co"))
    entities.append(LucjanSetpointSensor(coordinator, "cwu"))

    # Zawór 4D info sensors
    entities.append(LucjanConfigValueSensor(
        coordinator, "zawor4d_czujnik", "Zawór 4D — czujnik",
        "mdi:valve", lambda d: d.zawor4d_czujnik,
    ))
    entities.append(LucjanConfigValueSensor(
        coordinator, "zawor4d_preset", "Zawór 4D — preset",
        "mdi:valve", lambda d: f"{d.zawor4d_preset}%" if d.zawor4d_preset is not None else None,
    ))
    entities.append(LucjanConfigValueSensor(
        coordinator, "zawor4d_histereza", "Zawór 4D — histereza",
        "mdi:valve", lambda d: f"{d.zawor4d_histereza}°C" if d.zawor4d_histereza is not None else None,
    ))

    # Auto-lato info
    entities.append(LucjanConfigValueSensor(
        coordinator, "autolato_histereza", "Auto-lato — histereza",
        "mdi:sun-thermometer", lambda d: f"{d.autolato_histereza}°C" if d.autolato_histereza is not None else None,
    ))

    async_add_entities(entities)


class LucjanTemperatureSensor(LucjanEntity, SensorEntity):
    """Temperature sensor for one of 16 probes."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: LucjanCoordinator,
        sensor_key: str,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, sensor_key)
        self._attr_translation_key = sensor_key.lower()
        self._sensor_key = sensor_key

    @property
    def name(self) -> str:
        """Return sensor name."""
        return TEMP_SENSOR_NAMES.get(self._sensor_key, self._sensor_key)

    @property
    def native_value(self) -> float | None:
        """Return the sensor value."""
        if self.lucjan_data is None:
            return None
        return self.lucjan_data.temperatures.get(self._sensor_key)


class LucjanFanPowerSensor(LucjanEntity, SensorEntity):
    """Fan power percentage sensor."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:fan"

    def __init__(
        self,
        coordinator: LucjanCoordinator,
        key: str,
        name: str,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, key)
        self._attr_name = name
        self._fan_key = key

    @property
    def native_value(self) -> float | None:
        """Return fan power percentage."""
        if self.lucjan_data is None:
            return None
        if self._fan_key == "wen0":
            return self.lucjan_data.fan_power
        return self.lucjan_data.fan_modulation


class LucjanFuelConsumptionSensor(LucjanEntity, SensorEntity):
    """Total fuel consumption since boot in kg."""

    _attr_native_unit_of_measurement = UnitOfMass.KILOGRAMS
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_device_class = SensorDeviceClass.WEIGHT
    _attr_icon = "mdi:weight-kilogram"

    def __init__(self, coordinator: LucjanCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator, "fuel_consumption")
        self._attr_name = "Zużycie opału"

    @property
    def native_value(self) -> float | None:
        """Return fuel consumption in kg."""
        if self.lucjan_data is None:
            return None
        return self.lucjan_data.fuel_consumption_kg


class LucjanFeederTimeSensor(LucjanEntity, SensorEntity):
    """Feeder total working time in seconds."""

    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_icon = "mdi:timer-outline"

    def __init__(self, coordinator: LucjanCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator, "feeder_time")
        self._attr_name = "Czas podajnika"

    @property
    def native_value(self) -> float | None:
        """Return feeder time in seconds."""
        if self.lucjan_data is None:
            return None
        return self.lucjan_data.feeder_time_s


class LucjanHopperLevelSensor(LucjanEntity, SensorEntity):
    """Hopper (zasobnik) fill level percentage."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:gauge"

    def __init__(self, coordinator: LucjanCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator, "hopper_level")
        self._attr_name = "Poziom zasobnika"

    @property
    def native_value(self) -> float | None:
        """Return hopper level percentage."""
        if self.lucjan_data is None:
            return None
        return self.lucjan_data.hopper_level_percent


class LucjanUptimeSensor(LucjanEntity, SensorEntity):
    """System uptime sensor."""

    _attr_icon = "mdi:clock-outline"

    def __init__(self, coordinator: LucjanCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator, "uptime")
        self._attr_name = "Czas pracy"

    @property
    def native_value(self) -> str | None:
        """Return formatted uptime."""
        if self.lucjan_data is None:
            return None
        return self.lucjan_data.uptime_formatted


class LucjanFirmwareSensor(LucjanEntity, SensorEntity):
    """Firmware version sensor."""

    _attr_icon = "mdi:information-outline"

    def __init__(self, coordinator: LucjanCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator, "firmware")
        self._attr_name = "Wersja firmware"
        self._attr_entity_registry_enabled_default = False

    @property
    def native_value(self) -> str | None:
        """Return firmware version."""
        if self.lucjan_data is None:
            return None
        return self.lucjan_data.firmware_version


class LucjanAlgorithmSensor(LucjanEntity, SensorEntity):
    """Current algorithm sensor."""

    _attr_icon = "mdi:cog-outline"

    def __init__(self, coordinator: LucjanCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator, "algorithm")
        self._attr_name = "Algorytm pieca"

    @property
    def native_value(self) -> str | None:
        """Return current algorithm."""
        if self.lucjan_data is None:
            return None
        return self.lucjan_data.algorithm


class LucjanBoilerModeSensor(LucjanEntity, SensorEntity):
    """Current boiler mode sensor."""

    _attr_icon = "mdi:fire"

    def __init__(self, coordinator: LucjanCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator, "boiler_mode")
        self._attr_name = "Tryb pieca"

    @property
    def native_value(self) -> str | None:
        """Return current boiler mode."""
        if self.lucjan_data is None:
            return None
        return self.lucjan_data.boiler_mode


class LucjanSetpointSensor(LucjanEntity, SensorEntity):
    """Setpoint temperature sensor (read from config)."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_icon = "mdi:thermometer-check"

    def __init__(
        self, coordinator: LucjanCoordinator, kind: str
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, f"setpoint_{kind}")
        self._kind = kind
        if kind == "co":
            self._attr_name = "Temperatura zadana CO"
        else:
            self._attr_name = "Temperatura zadana CWU"

    @property
    def native_value(self) -> float | None:
        """Return setpoint temperature."""
        if self.lucjan_data is None:
            return None
        if self._kind == "co":
            return self.lucjan_data.target_temp_co
        return self.lucjan_data.target_temp_cwu


class LucjanConfigValueSensor(LucjanEntity, SensorEntity):
    """Generic sensor for config-derived string values."""

    def __init__(
        self,
        coordinator: LucjanCoordinator,
        key: str,
        name: str,
        icon: str,
        value_fn: Callable,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, key)
        self._attr_name = name
        self._attr_icon = icon
        self._value_fn = value_fn

    @property
    def native_value(self) -> str | None:
        """Return the value."""
        if self.lucjan_data is None:
            return None
        return self._value_fn(self.lucjan_data)
