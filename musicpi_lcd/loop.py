import time

import Adafruit_CharLCD as LCD

from musicpi_lcd.util import buttons

class Loop(object):
    def __init__(self, **kwargs):
        self.autochange = -1
        self.thresh_lo  = 2
        self.thresh_hi  = 3
        self.timeout    = -1
        self.__dict__.update(kwargs)
        
        self.reset()

    def reset(self):
        if self.timeout < 0:
            self.timeout = 15/self.ticklength
        if self.autochange < 0:
            self.autochange = 5/self.ticklength
        self.autocounter = 0
        self.thresh      = [self.thresh_lo]*len(buttons)
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
            if btn == LCD.SELECT:
                self.next_printer()
        else:
            self.state = 1
            self.do_init = True
        
    def update_button(self,btnmask,btn):
        if btnmask & (1 << btn):
            self.button_pressed(btn)
    
    def update_button_thresh(self,btnmask,btn):
        if btnmask & (1 << btn):
            self.btncounter[btn] += 1
            if self.btncounter[btn] >= self.thresh[btn]:
                self.button_pressed(btn)
                self.thresh[btn]     = self.thresh_hi
                self.btncounter[btn] = 0
        else:
            self.thresh[btn]     = self.thresh_lo
            self.btncounter[btn] = 0
            
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
