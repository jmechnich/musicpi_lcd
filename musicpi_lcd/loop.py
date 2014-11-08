import time

import Adafruit_CharLCD as LCD

from musicpi_lcd.util import buttons

class Loop(object):
    def __init__(self, **kwargs):
        self.autochange = -1
        self.longpress  =  2
        self.timeout    = -1
        self.__dict__.update(kwargs)
        
        self.reset()

    def reset(self):
        if self.timeout < 0:
            self.timeout = 15/self.ticklength
        if self.autochange < 0:
            self.autochange = 5/self.ticklength
        self.autocounter = 0
        self.btncounter  = [0]*len(buttons)
        self.offcounter  = 0
        
        self.do_init     = True
        self.idx         = 0
        self.state       = True
    
    def read_buttons(self):
        btnmask = 0
        for btn in xrange(len(buttons)):
            if self.lcd.is_pressed(btn):
                btnmask |= 1 << btn
        return btnmask

    def button_pressed(self,btn):
        self.offcounter = 0
        self.autochange = 0
        if self.state:
            self.printers[self.idx].button_pressed(btn)
        else:
            self.state = 1
            self.do_init = True
            self.btncounter[btn] = 0
        
    def button_pressed_long(self,btn):
        if self.state:
            self.printers[self.idx].button_pressed_long(btn)
            if btn == LCD.SELECT:
                self.next_printer()
        
    def button_released(self,btn, longpress):
        if self.state:
            if not longpress:
                self.printers[self.idx].button_clicked(btn)
            else:
                self.printers[self.idx].button_released(btn)

    def update_button(self,btnmask,btn):
        if btnmask & (1 << btn):
            self.btncounter[btn] += 1
            if self.btncounter[btn] == 1:
                if self.state:
                    self.lcd.set_backlight(0)
                    time.sleep(0.01)
                    self.lcd.set_color( *(self.printers[self.idx].color))
                else:
                    self.button_pressed(btn)
                    return
                self.button_pressed(btn)
            elif self.btncounter[btn] == self.longpress:
                self.button_pressed_long(btn)
            self.update_button.last[btn] = 1
        else:
            if self.update_button.last.get(btn, 0):
                self.button_released(btn, self.btncounter[btn] >= self.longpress)
                self.btncounter[btn] = 0
            self.update_button.last[btn] = 0
    update_button.last = {}
    
    def init_printer(self):
        self.printers[self.idx].init()
        self.do_init = False
    
    def next_printer(self):
        self.idx = (self.idx+1)%len(self.printers)
        self.do_init = True
        
    def iterate_autocounter(self):
        self.autocounter = (self.autocounter+1)%self.autochange
        if self.autocounter == 0:
            self.next_printer()

    def iterate_timeout(self):
        if self.timeout == 0:
            return self.state
        self.offcounter += 1
        if self.offcounter > self.timeout:
            self.state = 0
            self.offcounter = 0
            self.lcd.clear()
            self.lcd.set_backlight(0)
        return self.state
        
    def iterate(self):
        btnmask = self.read_buttons()
        for btn in xrange(len(buttons)):
            self.update_button(btnmask,btn)
        
        if self.iterate_timeout():
            if self.autochange > 0:
                self.iterate_autocounter()
        
            if self.do_init:
                self.init_printer()
            
            self.printers[self.idx].iterate()
        
        time.sleep(self.ticklength)
