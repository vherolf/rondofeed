"""Einstellungen der rondOfeed-Firmware. Alle Werte sind Startwerte und muessen am Aufbau geprueft werden."""

FW_VERSION = "0.1"
PROTO_VERSION = 1

# Pins des Pico, siehe PLAN.md
PIN_STEP = 2
PIN_DIR = 3
PIN_EN = 4        # TMC2209 EN, low = Treiber an, 10 kOhm nach 3V3 haelt ihn beim Booten aus
PIN_DIAG = 5
PIN_BEAM = 6      # Lichtschranke im Auslauf

# Motor: 0,9 Grad NEMA 17 mit 1/16 Mikroschritt
MICROSTEPS_PER_REV = 6400
DIR_FORWARD = 1   # Pegel von DIR fuer die Vorwaertsrichtung der Scheibe, am Aufbau pruefen
STEP_RATE_MIN = 300     # Schritte pro Sekunde am Anfang und Ende einer Fahrt
STEP_RATE_MAX = 2000    # Reisegeschwindigkeit, die schwere Scheibe braucht eine sanfte Rampe
RAMP_STEPS = 60         # Laenge der Rampe in Mikroschritten, kurze Fahrten bekommen weniger
RAMP_SECTIONS = 6       # Stufen je Rampe
ENABLE_SETTLE_MS = 10   # Wartezeit nach dem Einschalten des Treibers
DISABLE_DELAY_MS = 20   # Wartezeit nach der Fahrt bis der Treiber wieder aus ist

# Scheibe: Loecher je Scheibe, Position 0 ist geschlossen, siehe README
DEFAULT_PORTIONS = 47

# Lichtschranke
BEAM_BROKEN_LEVEL = 0   # Pegel am Pin, wenn der Strahl unterbrochen ist, am Sensor pruefen
BEAM_DEBOUNCE_MS = 20
BEAM_TIMEOUT_MS = 4000  # solange wartet ein Feed nach dem Schritt auf eine Portion
BEAM_SETTLE_MS = 500    # nach der ersten Portion noch so lange weiterzaehlen
RETRY_EXTRA = 0         # weitere Positionen, die bei ausbleibender Portion versucht werden (0 = nur melden)

# Grenzen, gelten fuer jede Quelle
MAX_PER_REQUEST = 10
MAX_PER_HOUR = 60       # gezaehlt ab dem Start, der Pico hat keine Uhr
MIN_GAP_MS = 500        # Mindestabstand zwischen zwei Feed-Anfragen
JOG_MAX = 800           # groesster Wert fuer JOG in Mikroschritten

WATCHDOG_MS = 8000      # 0 schaltet den Watchdog aus, zum Entwickeln hilfreich

BLE_NAME = "rondOfeed"
BLE_SERVICE = "7a1c0001-5a3e-4c6b-9d21-0f3c2a8e0001"
BLE_RX = "7a1c0002-5a3e-4c6b-9d21-0f3c2a8e0001"   # App schreibt Befehle
BLE_TX = "7a1c0003-5a3e-4c6b-9d21-0f3c2a8e0001"   # Pico meldet Antworten und Ereignisse
