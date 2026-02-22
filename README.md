# Lucjan Boiler Controller - Home Assistant Integration

[![HACS Custom][hacs-badge]][hacs-url]

Integracja Home Assistant dla sterownika pieca CO **Lucjan** (projekt [uzi18/sterownik](https://github.com/uzi18/sterownik)) opartego na Arduino Mega.

## Funkcje

### Encje Climate (termostat)
- **Piec CO** — aktualna temperatura pieca (`tPIEC`), temperatura zadana (`PIEC_ZADANA`), zakres 30–80 °C
- **CWU** — aktualna temperatura CWU (`tCWU`), temperatura zadana (`CWU_ZADANA`), zakres 30–65 °C

### Sensory temperatury (16 czujników)
| Klucz | Opis |
|-------|------|
| `tPIEC` | Temperatura pieca |
| `tPOWROT` | Temperatura powrotu |
| `tPODAJNIK` | Temperatura podajnika |
| `tZEW` | Temperatura zewnętrzna |
| `tWEW` | Temperatura wewnętrzna |
| `tCWU` | Temperatura CWU |
| `tPODLOGA` | Temperatura podłogi |
| `tSPALINY` | Temperatura spalin |
| `tT1`–`tT8` | Dodatkowe sondy temperatury |

### Sensory dodatkowe
- Moc wentylatora (%)
- Modulacja wentylatora (%)
- Zużycie opału (kg, total increasing)
- Czas pracy podajnika (s, total increasing)
- Poziom zasobnika (%)
- Czas pracy sterownika (uptime)
- Wersja firmware
- Algorytm pieca
- Tryb pieca (AUTO / RECZNY)
- Temperatury zadane CO i CWU (odczyt z konfiguracji)
- Zawór 4D — czujnik, preset, histereza
- Auto-lato — histereza

### Sensory binarne
| Encja | Opis |
|-------|------|
| Pompa CO | Stan pompy CO |
| Pompa CWU1 | Stan pompy CWU 1 |
| Pompa CWU2 | Stan pompy CWU 2 |
| Pompa cyrkulacyjna | Stan pompy cyrkulacyjnej |
| Podajnik | Stan podajnika |
| Termostat | Stan termostatu |
| Alarm | Stan alarmu (device class: problem) |

### Przełączniki (switch)
| Encja | Opis | Tryb |
|-------|------|------|
| Tryb AUTO | Przełączanie AUTO / RĘCZNY | zawsze |
| Pompa CO | Sterowanie pompą CO | tylko RĘCZNY |
| Pompa CWU | Sterowanie pompą CWU | tylko RĘCZNY |
| Pompa CWU2 | Sterowanie pompą CWU2 | tylko RĘCZNY |
| Pompa cyrkulacyjna | Sterowanie pompą cyrkulacyjną | tylko RĘCZNY |
| Podajnik | Sterowanie podajnikiem | tylko RĘCZNY |
| Priorytet CWU | Priorytet CWU (WLACZ / WYLACZ) | zawsze |
| Obwód CO + zawór 4D | Włączenie obwodu CO z zaworem 4D | zawsze |

> Przełączniki oznaczone „tylko RĘCZNY" są niedostępne w trybie AUTO.

### Przyciski (button)
| Encja | Opis |
|-------|------|
| Reset alarmu | Reset alarmu (`/alarmreset`) |
| Przeładuj konfigurację | Przeładowanie config.txt (`/configreload`) |
| Zasobnik do pełna | Oznaczenie zasobnika jako pełny (`/zasobnikfull`) |
| Reset sterownika | Reset sterownika (`/reset`) — domyślnie wyłączony |

### Suwaki (number)
| Encja | Zakres | Parametr | Tryb |
|-------|--------|----------|------|
| Moc wentylatora | 0–100 % | `OUT_WENTYLATOR` (runtime) | tylko RĘCZNY |
| Zawór 4D — temperatura zadana | 25–60 °C | `ZAWOR4D-ZADANA` | zawsze |
| Auto-lato — próg temp. zewnętrznej | 5–25 °C | `AUTOLATO_TEMP` | zawsze |
| Auto-lato — próg temp. wewnętrznej | 18–30 °C | `AUTOLATO_TWEW` | zawsze |
| Piec — temperatura maksymalna | 60–95 °C | `PIEC_T_MAX` | zawsze |
| Piec — temp. załączenia pomp | 30–55 °C | `PIEC_T_MIN` | zawsze |
| Cyrkulacja — min. temp. CWU | 20–60 °C | `CYRKULACJA_TMIN` | zawsze |
| CWU — temperatura maksymalna | 40–95 °C | `CWU_T_MAX` | zawsze |

### Listy wyboru (select)
| Encja | Opcje | Parametr |
|-------|-------|----------|
| Tryb CO | ZIMA, LATO, ECOAL, BRULI | `CO_TRYB` |
| Tryb CWU | WLACZ, WYLACZ, BRULI, ECOAL, MIESZANIE | `CWU_TRYB` |
| Algorytm palnika | RRM, RRM2, RR, ECOAL, ZASYPOWY, WYLACZONY | `PIEC_ALGORYTM` |
| Tryb zaworu 4D | ZADANA, KRZYWA, WYLACZONY | `ZAWOR4D-TRYB` |
| Cyrkulacja CWU | CIAGLY, CYKLICZNY, WYLACZONY | `CYRKULACJA_ALGORYTM` |
| Algorytm pompy CO | CIAGLY, CYKLICZNY | `CO_ALGORYTM` |
| Algorytm pompy CWU | CIAGLY, CYKLICZNY | `CWU_ALGORYTM` |

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
3. Podaj adres IP sterownika, login i hasło (domyślnie `admin`/`admin`)
4. Ustaw interwał aktualizacji (domyślnie 30 s, zakres 10–300 s)

Interwał aktualizacji można zmienić później w opcjach integracji.

## API sterownika

Integracja komunikuje się ze sterownikiem przez HTTP (Basic Auth):

| Metoda | Endpoint | Opis |
|--------|----------|------|
| `GET` | `/thermos.json` | Odczyt statusu (temperatury, stany pomp, wentylator, zasobnik) |
| `GET` | `/config.txt` | Odczyt konfiguracji (nastawy, algorytmy, tryby) |
| `GET` | `/setPARAMETR=wartość` | Ustawienie zmiennej runtime (np. `OUT_WENTYLATOR`) |
| `PUT` | `/upload/config.txt` | Upload zmodyfikowanej konfiguracji |
| `GET` | `/configreload` | Przeładowanie konfiguracji z pliku |
| `GET` | `/alarmreset` | Reset alarmu |
| `GET` | `/zasobnikfull` | Zasobnik do pełna |
| `GET` | `/reset` | Reset sterownika |

**Zmiana parametrów konfiguracyjnych** (np. `PIEC_ZADANA`, `CO_TRYB`) odbywa się przez pobranie `config.txt`, modyfikację wartości, upload (`PUT /upload/config.txt`) i przeładowanie (`/configreload`).

**Zmienne runtime** (np. `OUT_WENTYLATOR`, sterowanie pompami) ustawiane są bezpośrednio przez `/setPARAMETR=wartość` — nie są zapisywane na stałe.

## Diagnostyka

Integracja wspiera diagnostykę HA — dump danych dostępny w **Ustawienia → Urządzenia → Lucjan → Diagnostyka**.

## Licencja

MIT

## Podziękowania

- [uzi18](https://github.com/uzi18) — autor sterownika Lucjan
- Społeczność Home Assistant

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs-url]: https://github.com/hacs/integration
