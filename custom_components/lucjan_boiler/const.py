"""Constants for the Lucjan Boiler integration."""

DOMAIN = "lucjan_boiler"
MANUFACTURER = "uzi18"

# Config keys
CONF_HOST = "host"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SCAN_INTERVAL = "scan_interval"

# Defaults
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin"
DEFAULT_SCAN_INTERVAL = 30  # seconds
DEFAULT_PORT = 80

# API endpoints
ENDPOINT_THERMOS = "/thermos.json"
ENDPOINT_CONFIG = "/config.txt"

# Alarm field
ALARM_KEY = "al"

# Platforms
PLATFORMS = ["sensor", "binary_sensor", "climate", "switch", "button", "number", "select"]
TEMP_SENSORS = [
    "tPIEC",
    "tPOWROT",
    "tPODAJNIK",
    "tZEW",
    "tWEW",
    "tCWU",
    "tPODLOGA",
    "tSPALINY",
    "tT1",
    "tT2",
    "tT3",
    "tT4",
    "tT5",
    "tT6",
    "tT7",
    "tT8",
]

TEMP_SENSOR_NAMES = {
    "tPIEC": "Temperatura pieca",
    "tPOWROT": "Temperatura powrotu",
    "tPODAJNIK": "Temperatura podajnika",
    "tZEW": "Temperatura zewnętrzna",
    "tWEW": "Temperatura wewnętrzna",
    "tCWU": "Temperatura CWU",
    "tPODLOGA": "Temperatura podłogi",
    "tSPALINY": "Temperatura spalin",
    "tT1": "Temperatura T1",
    "tT2": "Temperatura T2",
    "tT3": "Temperatura T3",
    "tT4": "Temperatura T4",
    "tT5": "Temperatura T5",
    "tT6": "Temperatura T6",
    "tT7": "Temperatura T7",
    "tT8": "Temperatura T8",
}

# Binary sensor keys from thermos.json
BINARY_SENSORS = {
    "co": "Pompa CO",
    "cwu1": "Pompa CWU1",
    "cwu2": "Pompa CWU2",
    "cyrk": "Pompa cyrkulacyjna",
    "pod": "Podajnik",
    "ter": "Termostat",
}

