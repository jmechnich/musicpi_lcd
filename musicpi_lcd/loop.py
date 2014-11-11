import time

from musicpi_lcd.lcd  import LCD, buttons

class Loop(object):
    def __init__(self, **kwargs):
        self.ticklength  =   0.1
        self.iteratediv  =   10
        self.autochange  =  -1
        self.longpress   =  10
        self.repeatrate  =  5
        self.timeout     =  -1
        self.__dict__.update(kwargs)
        
        self.reset()

    def reset(self):
        if self.timeout < 0:
            self.timeout    = round(15/self.ticklength)
        if self.autochange < 0:
            self.autochange = round(5/self.ticklength)
        self.autocounter    = 0
        self.btncounter     = [0]*len(buttons)
        self.offcounter     = 0
        self.updatecounter  = 0
        self.last           = {}

        self.do_init        = True
        self.idx            = 0
        self.state          = True
    
    def read_buttons(self):
        btnmask = 0
        for btn in xrange(len(buttons)):
            if self.lcd.is_pressed(btn):
                btnmask |= 1 << btn
        return btnmask

    def button_pressed(self,btn,repeat=False):
        if self.debug:
            print "Button %d pressed (repeat: %s)" % (btn,str(repeat))
        self.offcounter = 0
        self.autochange = 0
        if self.state:
            self.printers[self.idx].button_pressed(btn, repeat)
        else:
            self.state = 1
            self.do_init = True
            self.btncounter[btn] = 0
            self.last[btn] = -1
            
    def button_pressed_long(self,btn):
        if self.debug:
            print "Button", btn, "pressed long"
        if self.state:
            self.printers[self.idx].button_pressed_long(btn)
            if btn == LCD.SELECT:
                self.next_printer()
        
    def button_released(self,btn,longpress):
        if self.debug:
            print "Button", btn, "released"
        if self.state:
            if longpress:
                self.printers[self.idx].button_released(btn)
            else:
                self.printers[self.idx].button_clicked(btn)

    def blink(self):
        if not self.state:
            return
        backlight = False
        if backlight:
            self.lcd.set_backlight(0)
            time.sleep(0.01)
            self.lcd.set_color( *(self.printers[self.idx].color))
        else:
            self.lcd.enable_display(False)
            time.sleep(0.01)
            self.lcd.enable_display(True)
    def update_button(self,btnmask,btn):
        pressed = btnmask & (1 << btn)
        if pressed:
            self.btncounter[btn] += 1
        
        count  = self.btncounter[btn] 
        last   = self.last.get(btn, 0)
        repeat = (count >= self.longpress)
        if pressed:
            if last < 0: return
            self.last[btn] = 1
            if count == 1:
                self.blink()
                self.button_pressed(btn, False)
                return
            if count == self.longpress:
                self.button_pressed_long(btn)
            if repeat and (self.repeatrate and (count-self.longpress)%self.repeatrate == 0):
                self.button_pressed(btn, True)
        elif last != 0:
            if last > 0:
                self.button_released(btn, count >= self.longpress or repeat)
                self.btncounter[btn] = 0
            self.last[btn] = 0
    
    def init_printer(self):
        if self.debug:
            print "Initializing", type(self.printers[self.idx]).__name__
        self.printers[self.idx].init()
        self.do_init = False
    
    def next_printer(self):
        if self.debug:
            print "Changing to next printer"
        self.printers[self.idx].stop()
        self.idx = (self.idx+1)%len(self.printers)
        self.do_init = True
        
    def iterate_autocounter(self):
        self.autocounter = (self.autocounter+1)%self.autochange
        if self.autocounter == 0:
            self.next_printer()

    def iterate_timeout(self):
        if self.timeout == 0 or not self.state:
            return self.state
        self.offcounter += 1
        if self.offcounter > self.timeout:
            self.state = 0
            self.offcounter = 0
            self.lcd.clear()
            self.lcd.set_backlight(0)
        return self.state
        
    def iterate(self):
        #if self.debug: print type(self).__name__, 'iterate'
        btnmask = self.read_buttons()
        for btn in xrange(len(buttons)):
            self.update_button(btnmask,btn)
        
        if self.iterate_timeout():
            if self.autochange > 0:
                self.iterate_autocounter()
        
            if self.do_init:
                self.init_printer()
                self.printers[self.idx].iterate()
                self.updatecounter = 0
            
            if self.updatecounter == 0:
                self.printers[self.idx].iterate()
            self.updatecounter = (self.updatecounter+1)%self.iteratediv
            
        time.sleep(self.ticklength)
