# License : GPLv2.0
# copyright (c) 2023  Dave Bailey
# Author: Dave Bailey (dbisu, @daveisu)

import time
import digitalio
from digitalio import DigitalInOut, Pull
from adafruit_debouncer import Debouncer
import board
from board import *
import pwmio
import asyncio
import usb_hid
from adafruit_hid.keyboard import Keyboard

# comment out these lines for non-US keyboards
# from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS as KeyboardLayout
# from adafruit_hid.keycode import Keycode

# uncomment these lines for non-US keyboards
# replace LANG with appropriate language
from keyboard_layout_win_de import KeyboardLayout
from keycode_win_de import Keycode

duckyCommands = {
    'WINDOWS': Keycode.WINDOWS, 'GUI': Keycode.GUI,
    'APP': Keycode.APPLICATION, 'MENU': Keycode.APPLICATION, 'SHIFT': Keycode.SHIFT,
    'ALT': Keycode.ALT, 'CONTROL': Keycode.CONTROL, 'CTRL': Keycode.CONTROL,
    'DOWNARROW': Keycode.DOWN_ARROW, 'DOWN': Keycode.DOWN_ARROW, 'LEFTARROW': Keycode.LEFT_ARROW,
    'LEFT': Keycode.LEFT_ARROW, 'RIGHTARROW': Keycode.RIGHT_ARROW, 'RIGHT': Keycode.RIGHT_ARROW,
    'UPARROW': Keycode.UP_ARROW, 'UP': Keycode.UP_ARROW, 'BREAK': Keycode.PAUSE,
    'PAUSE': Keycode.PAUSE, 'CAPSLOCK': Keycode.CAPS_LOCK, 'DELETE': Keycode.DELETE,
    'END': Keycode.END, 'ESC': Keycode.ESCAPE, 'ESCAPE': Keycode.ESCAPE, 'HOME': Keycode.HOME,
    'INSERT': Keycode.INSERT, 'NUMLOCK': Keycode.KEYPAD_NUMLOCK, 'PAGEUP': Keycode.PAGE_UP,
    'PAGEDOWN': Keycode.PAGE_DOWN, 'PRINTSCREEN': Keycode.PRINT_SCREEN, 'ENTER': Keycode.ENTER,
    'SCROLLLOCK': Keycode.SCROLL_LOCK, 'SPACE': Keycode.SPACE, 'TAB': Keycode.TAB,
    'BACKSPACE': Keycode.BACKSPACE,
    'A': Keycode.A, 'B': Keycode.B, 'C': Keycode.C, 'D': Keycode.D, 'E': Keycode.E,
    'F': Keycode.F, 'G': Keycode.G, 'H': Keycode.H, 'I': Keycode.I, 'J': Keycode.J,
    'K': Keycode.K, 'L': Keycode.L, 'M': Keycode.M, 'N': Keycode.N, 'O': Keycode.O,
    'P': Keycode.P, 'Q': Keycode.Q, 'R': Keycode.R, 'S': Keycode.S, 'T': Keycode.T,
    'U': Keycode.U, 'V': Keycode.V, 'W': Keycode.W, 'X': Keycode.X, 'Y': Keycode.Y,
    'Z': Keycode.Z, 'F1': Keycode.F1, 'F2': Keycode.F2, 'F3': Keycode.F3,
    'F4': Keycode.F4, 'F5': Keycode.F5, 'F6': Keycode.F6, 'F7': Keycode.F7,
    'F8': Keycode.F8, 'F9': Keycode.F9, 'F10': Keycode.F10, 'F11': Keycode.F11,
    'F12': Keycode.F12,
}

def convertLine(line):
    newline = []
    # Split the line by space to handle individual keys
    for key_group in filter(None, line.split(" ")):
        # Check if the key group is a combo (e.g., "GUI R")
        if "+" in key_group:
            combo_keys = key_group.split("+")
            for combo_key in combo_keys:
                combo_key = combo_key.upper()
                # Lookup each combo key
                command_keycode = duckyCommands.get(combo_key, None)
                if command_keycode is not None:
                    newline.append(command_keycode)
                else:
                    print(f"Unknown key: <{combo_key}>")
        else:
            key = key_group.upper()
            # Handle non-combo keys normally
            command_keycode = duckyCommands.get(key, None)
            if command_keycode is not None:
                newline.append(command_keycode)
            else:
                print(f"Unknown key: <{key}>")
    return newline


def runScriptLine(line):
    typing_delay = 0.1  # Adjust this delay for key timing
    for k in line:
        kbd.press(k)
        time.sleep(typing_delay)
        kbd.release(k)
    kbd.release_all()

def sendString(line):
    layout.write(line)

def parseLine(line):
    global defaultDelay
    if line.startswith("REM"):
        pass  # Ignore comments
    elif line.startswith("DELAY"):
        time.sleep(float(line[6:]) / 1000)
    elif line.startswith("STRING"):
        sendString(line[7:])
    elif line.startswith("PRINT"):
        print("[SCRIPT]: " + line[6:])
    elif line.startswith("IMPORT"):
        runScript(line[7:])
    elif line.startswith("DEFAULT_DELAY"):
        defaultDelay = int(line[14:]) * 10
    elif line.startswith("DEFAULTDELAY"):
        defaultDelay = int(line[13:]) * 10
    elif line.startswith("LED"):
        led.value = not led.value
    else:
        newScriptLine = convertLine(line)
        runScriptLine(newScriptLine)

kbd = Keyboard(usb_hid.devices)
layout = KeyboardLayout(kbd)

# Init button
button1_pin = DigitalInOut(GP22)
button1_pin.pull = Pull.UP
button1 = Debouncer(button1_pin)

# Init payload selection switch
payload1Pin = digitalio.DigitalInOut(GP4)
payload1Pin.switch_to_input(pull=digitalio.Pull.UP)
payload2Pin = digitalio.DigitalInOut(GP5)
payload2Pin.switch_to_input(pull=digitalio.Pull.UP)
payload3Pin = digitalio.DigitalInOut(GP10)
payload3Pin.switch_to_input(pull=digitalio.Pull.UP)
payload4Pin = digitalio.DigitalInOut(GP11)
payload4Pin.switch_to_input(pull=digitalio.Pull.UP)

def getProgrammingStatus():
    progStatusPin = digitalio.DigitalInOut(GP0)
    progStatusPin.switch_to_input(pull=digitalio.Pull.UP)
    return not progStatusPin.value

defaultDelay = 0

def runScript(file):
    global defaultDelay
    try:
        with open(file, "r", encoding='utf-8') as f:
            previousLine = ""
            for line in f:
                line = line.rstrip()
                if line.startswith("REPEAT"):
                    for i in range(int(line[7:])):
                        parseLine(previousLine)
                        time.sleep(float(defaultDelay) / 1000)
                else:
                    parseLine(line)
                    previousLine = line
                time.sleep(float(defaultDelay) / 1000)
    except OSError as e:
        print(f"Unable to open file {file}")

def selectPayload():
    payload = "payload.dd"
    if not payload1Pin.value:
        payload = "payload.dd"
    elif not payload2Pin.value:
        payload = "payload2.dd"
    elif not payload3Pin.value:
        payload = "payload3.dd"
    elif not payload4Pin.value:
        payload = "payload4.dd"
    return payload

async def blink_led(led):
    if board.board_id == 'raspberry_pi_pico':
        await blink_pico_led(led)
    elif board.board_id == 'raspberry_pi_pico_w':
        await blink_pico_w_led(led)

async def blink_pico_led(led):
    led_state = False
    while True:
        if led_state:
            for i in range(100):
                if i < 50:
                    led.duty_cycle = int(i * 2 * 65535 / 100)
                await asyncio.sleep(0.01)
            led_state = False
        else:
            for i in range(100):
                if i >= 50:
                    led.duty_cycle = 65535 - int((i - 50) * 2 * 65535 / 100)
                await asyncio.sleep(0.01)
            led_state = True
        await asyncio.sleep(0)

async def blink_pico_w_led(led):
    led_state = False
    while True:
        led.value = 1 if led_state else 0
        await asyncio.sleep(0.5)
        led_state = not led_state

async def monitor_buttons(button1):
    button1Down = False
    while True:
        button1.update()
        if button1.fell:
            button1Down = True
        if button1.rose and button1Down:
            payload = selectPayload()
            runScript(payload)
            button1Down = False
        await asyncio.sleep(0)
