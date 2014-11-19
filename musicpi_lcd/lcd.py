import Adafruit_CharLCD as Base

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

class LCD(Base.Adafruit_RGBCharLCD):
    """Class to represent and interact with an Adafruit Raspberry Pi character
    LCD plate."""

    SELECT = Base.SELECT
    RIGHT  = Base.RIGHT
    DOWN   = Base.DOWN
    UP     = Base.UP
    LEFT   = Base.LEFT

    SYM_RIGHT = 0x0
    SYM_LEFT  = 0x1
    SYM_UP    = 0x2
    SYM_DOWN  = 0x3
    SYM_CLOCK = 0x4
    SYM_PLAY  = 0x5
    SYM_PAUSE = 0x6
    SYM_STOP  = 0x7

    def __init__(self, address=0x20, busnum=Base.I2C.get_default_bus(), cols=16, lines=2):
        """Initialize the character LCD plate.  Can optionally specify a separate
        I2C address or bus number, but the defaults should suffice for most needs.
        Can also optionally specify the number of columns and lines on the LCD
        (default is 16x2).
        """
        # Configure MCP23017 device.
        self._mcp = Base.MCP.MCP23017(address=address, busnum=busnum)
        # Make sure that LEDs are off
        self._mcp.setup(Base.LCD_PLATE_RED,   Base.GPIO.OUT)
        self._mcp.setup(Base.LCD_PLATE_GREEN, Base.GPIO.OUT)
        self._mcp.setup(Base.LCD_PLATE_BLUE,  Base.GPIO.OUT)
        val = Base.GPIO.HIGH
        self._mcp.output_pins({Base.LCD_PLATE_RED: val, Base.LCD_PLATE_GREEN: val, Base.LCD_PLATE_BLUE: val})
        # Set LCD R/W pin to low for writing only.
        self._mcp.setup(Base.LCD_PLATE_RW, Base.GPIO.OUT)
        self._mcp.output(Base.LCD_PLATE_RW, Base.GPIO.LOW)
        # Set buttons as inputs with pull-ups enabled.
        for button in (self.SELECT, self.RIGHT, self.DOWN, self.UP, self.LEFT):
            self._mcp.setup(button, Base.GPIO.IN)
            self._mcp.pullup(button, True)
        # Initialize LCD (with no PWM support).
        super(LCD, self).__init__(Base.LCD_PLATE_RS, Base.LCD_PLATE_EN,
                                  Base.LCD_PLATE_D4, Base.LCD_PLATE_D5, Base.LCD_PLATE_D6, Base.LCD_PLATE_D7, cols, lines,
                                  Base.LCD_PLATE_RED, Base.LCD_PLATE_GREEN, Base.LCD_PLATE_BLUE, enable_pwm=False, 
            gpio=self._mcp,initial_color=colors['black'])
        self.clear()

        self.create_char(self.SYM_RIGHT, [0x0,0x8,0xc,0xe,0xc,0x8,0x0,0x0])
        self.create_char(self.SYM_LEFT,  [0x0,0x2,0x6,0xe,0x6,0x2,0x0,0x0])
        self.create_char(self.SYM_UP,    [0x0,0x0,0x4,0xe,0x1f,0x0,0x0,0x0])
        self.create_char(self.SYM_DOWN,  [0x0,0x0,0x1f,0xe,0x4,0x0,0x0,0x0])
        self.create_char(self.SYM_CLOCK, [0x0,0xe,0x15,0x17,0x11,0xe,0x0,0x0])
        self.create_char(self.SYM_PLAY,  [0x8,0xc,0xe,0xf,0xe,0xc,0x8,0x0])
        self.create_char(self.SYM_PAUSE, [0x1b,0x1b,0x1b,0x1b,0x1b,0x1b,0x1b,0x0])
        self.create_char(self.SYM_STOP,  [0x0,0x1f,0x1f,0x1f,0x1f,0x1f,0x0,0x0])
        
    def __del__(self):
        self.off()

    def is_pressed(self, button):
        """Return True if the provided button is pressed, False otherwise."""
        if button not in set((self.SELECT, self.RIGHT, self.DOWN, self.UP, self.LEFT)):
            raise ValueError('Unknown button, must be SELECT, RIGHT, DOWN, UP, or LEFT.')
        return self._mcp.input(button) == Base.GPIO.LOW

    def off(self):
        self.clear()
        self.set_backlight(0)
        
buttons = [ LCD.SELECT, LCD.RIGHT, LCD.DOWN, LCD.LEFT, LCD.UP ]

