import Adafruit_CharLCD as LCD

from musicpi_lcd.util import buttons, colors

class Printer(object):
    def __init__(self,**kwargs):
        self.delay = 0.3
        self.color = colors['white']
        self.__dict__.update(kwargs)
        
        self.pages = []
        self.active = -1
        self.tickcounter = 0
        self.btncounter = dict(zip(buttons,[0]*len(buttons)))
        self.longpress = 3
        
    def iterate(self):
        if self.tickcounter == 0:
            self.render()
        self.tickcounter += self.ticklength
        if self.tickcounter > self.delay:
            self.tickcounter = 0

    def render(self,force=False):
        if (self.active < 0) or (self.active >= len(self.pages)):
            return
        self.pages[self.active].render( 
            force=force,
            set_cursor_func=self.lcd.set_cursor,
            message_func=self.lcd.message,
            )
        
    def button_released(self,btn):
        pass
    
    def button_pressed(self,btn):
        pass
          
    def button_pressed_long(self,btn):
        if btn == LCD.RIGHT:
            self.next_page()
        elif btn == LCD.DOWN:
            pass
        elif btn == LCD.UP:
            pass
        elif btn == LCD.LEFT:
            self.prev_page()
            
    def button_clicked(self,btn):
        pass
          
    def prev_page(self):
        self.active -= 1
        if self.active < 0:
            self.active = len(self.pages)-1
        self.render(force=True)

    def next_page(self):
        self.active += 1
        if self.active >= len(self.pages):
            self.active = 0
        self.render(force=True)
