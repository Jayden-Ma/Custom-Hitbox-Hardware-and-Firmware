# Jayden Ma, hitbox firmware

# imports
import time
import board
import usb_hid
import adafruit_hid
import digitalio
from digitalio import DigitalInOut, Direction, Pull
from adafruit_hid.keycode import Keycode
from adafruit_hid.keyboard import Keyboard

import sys

# Select current profile in this field
currentProfile = "gaming";

# supported values for switches:
# Type 1: simple keys:        ('key', Keycode.A)
# Type 2: key combinations:   ('combo', [Keycode.CONTROL, Keycode.C])
# Type 3: string typing:      ('string', "Hello World!")

profiles = {
    # gaming profile
    "gaming" : [
    (1, board.GP8, ('key', Keycode.SPACE)),
    (2, board.GP7, ('key', Keycode.A)),
    (3, board.GP6, ('key', Keycode.S)),
    (4, board.GP5, ('key', Keycode.D)),
    (5, board.GP15, ('key', Keycode.W)),
    (6, board.GP16, ('key', Keycode.W)),
    (7, board.GP27, ('key', Keycode.J)),
    (8, board.GP26, ('key', Keycode.K)),
    (9, board.GP22, ('key', Keycode.L)),
    (10, board.GP21, ('key', Keycode.SPACE )),
    (11, board.GP20, ('key', Keycode.M)),
    (12, board.GP19, ('key', Keycode.COMMA)),
    (13, board.GP18, ('key', Keycode.PERIOD)),
    (14, board.GP17, ('key', Keycode.FORWARD_SLASH))
    ],

    # python coding profile
    "python" : [
    (1, board.GP8, ('string', "print(\"\")")),
    (2, board.GP7, ('string', "for i in range():\n# TODO: add code here\n")),
    (3, board.GP6, ('string', "def func():\n\'\'\'")),
    (4, board.GP5, ('string', "if :\nprint(\"\")")),
    (5, board.GP15, ('key', Keycode.RIGHT_SHIFT)),
    (6, board.GP16, ('key', Keycode.BACKSPACE)),
    (7, board.GP27, ('combo', [Keycode.CONTROL, Keycode.C])),
    (8, board.GP26, ('key', Keycode.UP_ARROW)),
    (9, board.GP22, ('combo', [Keycode.CONTROL, Keycode.V])),
    (10, board.GP21, ('combo', [Keycode.CONTROL, Keycode.FORWARD_SLASH])),
    (11, board.GP20, ('key', Keycode.LEFT_ARROW)),
    (12, board.GP19, ('key', Keycode.DOWN_ARROW)),
    (13, board.GP18, ('key', Keycode.RIGHT_ARROW)),
    (14, board.GP17, ('key', Keycode.ENTER))
    ]
}

keyboard = Keyboard(usb_hid.devices)

# built-in LED for activity feedback
builtInLED = digitalio.DigitalInOut(board.LED)
builtInLED.direction = digitalio.Direction.OUTPUT

# Load the selected profile
for profileKey in profiles:
    if currentProfile == profileKey:
        SWITCHES = profiles[profileKey]

# Create DigitalInOut objects for each switch with pull-up
switches = []
for switch in SWITCHES:
    sw = DigitalInOut(switch[1])   # second element = GPIO pin
    sw.direction = Direction.INPUT
    sw.pull = Pull.UP              # pull-up means pressed = LOW
    switches.append(sw)

print("start polling")

# Track previous key states to avoid repeated presses
pressed_states = [False] * len(SWITCHES)

# External LED on GP3 (used for feedback + timer flashing)
led = digitalio.DigitalInOut(board.GP3)
led.direction = digitalio.Direction.OUTPUT

# Keyboard layout helper (for typing strings)
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
layout = KeyboardLayoutUS(keyboard)

# --- Timer logic: flashes LED every 30 min (1800s) to track playtime ---
TIMER_INTERVAL = 1800      # time before LED flash (30 minutes)
FLASH_DURATION = 5         # LED stays on for 5 seconds
timer_start = time.monotonic()
flash_active = False
flash_end_time = 0

while True:
    # --- Timer logic ---
    now = time.monotonic()

    # Start LED flash when timer expires
    if not flash_active and (now - timer_start >= TIMER_INTERVAL):
        print("TIMER: Flash started")
        led.value = True
        flash_active = True
        flash_end_time = now + FLASH_DURATION

    # End flash and reset timer
    if flash_active and now >= flash_end_time:
        led.value = False
        flash_active = False
        timer_start = time.monotonic()

    # --- Main switch processing loop ---
    for idx, ((label, pin, info), sw) in enumerate(zip(SWITCHES, switches)):

        inputType = info[0]   # 'key', 'combo', or 'string'
        action = info[1]      # key value, combo list, or string

        # If pressed (LOW because of pull-up)
        if not sw.value:
            if not pressed_states[idx]:      # only trigger once per press
                print(f"SW{label} pressed")

                if inputType == "key":
                    led.value = True          # turn LED on (feedback)
                    keyboard.press(action)    # hold the key down

                elif inputType == "combo":
                    for kc in action:
                        keyboard.press(kc)    # press all keys
                    for kc in action:
                        keyboard.release(kc)  # and release them

                elif inputType == "string":
                    layout.write(action)      # type out text

                builtInLED.value = True       # turn on built-in LED
                pressed_states[idx] = True    # mark as pressed

        else:
            # On release
            if pressed_states[idx]:
                print(f"SW{label} released")

                if inputType == "key":
                    keyboard.release(action)  # release held key
                    led.value = False         # turn LED off

                builtInLED.value = False
                pressed_states[idx] = False   # mark as released

    time.sleep(0.005)    # tiny delay to avoid bouncing
