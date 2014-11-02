import time

import Adafruit_CharLCD as LCD

colors = {
    'black':   (0.0, 0.0, 0.0),
    'red':     (1.0, 0.0, 0.0),
    'green':   (0.0, 1.0, 0.0),
    'blue':    (0.0, 0.0, 1.0),
    'yellow':  (1.0, 1.0, 0.0),
    'cyan':    (0.0, 1.0, 1.0),
    'magenta': (1.0, 0.0, 1.0),
    'white':   (1.0, 1.0, 1.0),
}

buttons = [ LCD.SELECT, LCD.RIGHT, LCD.DOWN, LCD.LEFT, LCD.UP ]
