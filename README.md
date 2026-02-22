# Lucjan Boiler Controller - Home Assistant Integration

[![HACS Custom][hacs-badge]][hacs-url]

Integracja Home Assistant dla sterownika pieca CO **Lucjan** (projekt [uzi18/sterownik](https://github.com/uzi18/sterownik)) opartego na Arduino Mega.

## Funkcje

### Encje Climate (termostat)
- **Piec CO** — aktualna temperatura pieca, temperatura zadana, sterowanie nastawą
- **CWU** — aktualna temperatura CWU, temperatura zadana (jeśli skonfigurowane)

### Sensory temperatury (16 czujników)
- tPIEC, tPOWROT, tPODAJNIK, tZEW, tWEW, tCWU, tPODLOGA, tSPALINY, tT1–tT8

### Sensory dodatkowe
- Moc wentylatora (%)
- Modulacja wentylatora (%)
- Zużycie opału (kg)
- Czas pracy podajnika
- Poziom zasobnika (%)
- Czas pracy sterownika (uptime)
- Wersja firmware
- Algorytm pieca
- Tryb pieca
- Temperatury zadane CO i CWU

### Sensory binarne
- Pompa CO, CWU1, CWU2
- Pompa cyrkulacyjna
- Podajnik
- Termostat
- Alarm

### Przyciski
- Reset alarmu
- Przeładuj konfigurację
- Zasobnik do pełna
- Reset sterownika

### Kontrolki
- Nastawa mocy wentylatora (slider 0–100%)

## Wymagania

- Sterownik Lucjan z modułem Ethernet lub ESP-Link
- Sterownik dostępny po HTTP w sieci lokalnej
- Home Assistant 2024.6+

## Instalacja

### HACS (zalecane)

1. Otwórz HACS w Home Assistant
2. Kliknij **⋮** → **Repozytoria niestandardowe**
3. Dodaj URL repozytorium i wybierz kategorię **Integracja**
4. Zainstaluj **Lucjan Boiler Controller**
5. Restart Home Assistant

### Ręczna

1. Skopiuj folder `custom_components/lucjan_boiler` do `config/custom_components/`
2. Restart Home Assistant

## Konfiguracja

1. **Ustawienia → Urządzenia i usługi → Dodaj integrację**
2. Wyszukaj **Lucjan Boiler Controller**
3. Podaj adres IP sterownika, login i hasło (domyślnie admin/admin)
4. Ustaw interwał aktualizacji (domyślnie 30s)

## API sterownika

Integracja komunikuje się ze sterownikiem przez HTTP:
- `GET /thermos.json` — odczyt statusu (temperatury, stany, wentylator, zasobnik)
- `GET /config.txt` — odczyt konfiguracji (nastawy, algorytmy)
- `GET /setPARAMETR=wartość` — ustawienie parametru
- `GET /alarmreset` — reset alarmu
- `GET /configreload` — przeładowanie konfiguracji
- `GET /zasobnikfull` — zasobnik do pełna

## Diagnostyka

Integracja wspiera diagnostykę HA — dump danych dostępny w **Ustawienia → Urządzenia → Lucjan → Diagnostyka**.

## Licencja

MIT

## Podziękowania

- [uzi18](https://github.com/uzi18) — autor sterownika Lucjan
- Społeczność Home Assistant

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs-url]: https://github.com/hacs/integration
