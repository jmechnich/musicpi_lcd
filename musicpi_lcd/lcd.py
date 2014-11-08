
from Adafruit_CharLCD import *

from musicpi_lcd.util import colors

class LCD(Adafruit_RGBCharLCD):
    """Class to represent and interact with an Adafruit Raspberry Pi character
    LCD plate."""

    def __init__(self, address=0x20, busnum=I2C.get_default_bus(), cols=16, lines=2):
        """Initialize the character LCD plate.  Can optionally specify a separate
        I2C address or bus number, but the defaults should suffice for most needs.
        Can also optionally specify the number of columns and lines on the LCD
        (default is 16x2).
        """
        # Configure MCP23017 device.
        self._mcp = MCP.MCP23017(address=address, busnum=busnum)
        # Make sure that LEDs are off
        self._mcp.setup(LCD_PLATE_RED, GPIO.OUT)
        self._mcp.setup(LCD_PLATE_GREEN, GPIO.OUT)
        self._mcp.setup(LCD_PLATE_BLUE, GPIO.OUT)
        val = GPIO.HIGH
        self._mcp.output_pins({LCD_PLATE_RED: val, LCD_PLATE_GREEN: val, LCD_PLATE_BLUE: val})
        # Set LCD R/W pin to low for writing only.
        self._mcp.setup(LCD_PLATE_RW, GPIO.OUT)
        self._mcp.output(LCD_PLATE_RW, GPIO.LOW)
        # Set buttons as inputs with pull-ups enabled.
        for button in (SELECT, RIGHT, DOWN, UP, LEFT):
            self._mcp.setup(button, GPIO.IN)
            self._mcp.pullup(button, True)
        # Initialize LCD (with no PWM support).
        super(LCD, self).__init__(LCD_PLATE_RS, LCD_PLATE_EN,
            LCD_PLATE_D4, LCD_PLATE_D5, LCD_PLATE_D6, LCD_PLATE_D7, cols, lines,
            LCD_PLATE_RED, LCD_PLATE_GREEN, LCD_PLATE_BLUE, enable_pwm=False, 
            gpio=self._mcp,initial_color=colors['black'])
        self.clear()

    def __del__(self):
        self.off()

    def is_pressed(self, button):
        """Return True if the provided button is pressed, False otherwise."""
        if button not in set((SELECT, RIGHT, DOWN, UP, LEFT)):
            raise ValueError('Unknown button, must be SELECT, RIGHT, DOWN, UP, or LEFT.')
        return self._mcp.input(button) == GPIO.LOW

    def off(self):
        self.clear()
        self.set_backlight(0)
        
