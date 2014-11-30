import time

from lcd import LCD, buttons

class Loop(object):
    def __init__(self, **kwargs):
        self.ticklength  =   0.1
        self.iteratediv  =   2
        self.autochange  =  -1
        self.longpress   =  10
        self.repeatrate  =  5
        self.timeout     =  -1
        self.__dict__.update(kwargs)
        
        self.reset()

    def reset(self):
        if self.timeout < 0:
            self.timeout_real = round(15/self.ticklength)
        else:
            self.timeout_real = round(self.timeout/self.ticklength)
        if self.autochange < 0:
            self.autochange_real = round(5/self.ticklength)
        else:
            self.autochange_real = round(self.autochange/self.ticklength)
        self.autocounter    = 0
        self.btncounter     = [0]*len(buttons)
        self.offcounter     = 0
        self.updatecounter  = 0
        self.last           = {}

        self.do_init        = True
        self.idx            = 0
        self.state          = True
        if self.profile:
            self.prof = {}
            self.prof_time = {}
    
    def read_buttons(self):
        btnmask = 0
        for btn in xrange(len(buttons)):
            if self.lcd.is_pressed(btn):
                btnmask |= 1 << btn
        return btnmask

    def button_pressed(self,btn,repeat=False):
        self.logger.debug("Button %d pressed (repeat: %s)" % (btn,str(repeat)))
        self.offcounter = 0
        self.autochange = 0
        if self.state:
            self.printers[self.idx].button_pressed(btn, repeat)
        else:
            self.logger.info("Display activated")
            self.state = 1
            self.do_init = True
            self.btncounter[btn] = 0
            self.last[btn] = -1
            
    def button_pressed_long(self,btn):
        self.logger.debug( "Button %d pressed long" % btn)
        if self.state:
            self.printers[self.idx].button_pressed_long(btn)
            if btn == LCD.SELECT:
                self.next_printer()
        
    def button_released(self,btn,longpress):
        self.logger.debug( "Button %d released" % btn)
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
            if last < 0: return True
            self.last[btn] = 1
            if count == 1:
                self.blink()
                self.button_pressed(btn, False)
                return not self.printers[self.idx].exit
            if count == self.longpress:
                self.button_pressed_long(btn)
            if repeat and self.repeatrate and ((count-self.longpress)%self.repeatrate) == 0:
                self.button_pressed(btn, True)
        elif last != 0:
            if last > 0:
                self.button_released(btn, count >= self.longpress or repeat)
                self.btncounter[btn] = 0
            self.last[btn] = 0
        return not self.printers[self.idx].exit

    def init_printer(self):
        self.logger.debug("Initializing %s" % type(self.printers[self.idx]).__name__)
        self.printers[self.idx].init()
        self.do_init = False
    
    def next_printer(self):
        self.logger.debug( "Changing to next printer")
        self.printers[self.idx].stop()
        self.idx = (self.idx+1)%len(self.printers)
        self.do_init = True
        
    def iterate_autocounter(self):
        self.autocounter = (self.autocounter+1)%self.autochange_real
        if self.autocounter == 0:
            self.logger.debug("Autochange")
            self.next_printer()

    def iterate_timeout(self):
        if self.timeout_real == 0 or not self.state:
            return self.state
        self.offcounter += 1
        if self.offcounter > self.timeout_real:
            self.state = 0
            self.offcounter = 0
            self.lcd.off()
            self.logger.info("Display timeout")
        return self.state

    def profile_update(self, text):
        self.prof[text] = self.prof.get(text,0)
        cur_time = time.time()
        if not self.prof_time.has_key(text):
            self.prof_time[text] = cur_time
            return
        count = self.prof[text] + 1
        dt    = cur_time-self.prof_time[text]
        if dt > 1:
            freq  = count/dt
            ticks = self.ticklength*freq
            self.logger.info("Update frequency %s: %.2f Hz (%.2f ticks)" % (text,freq,ticks))
            count = 0
            self.prof_time[text] = cur_time
        self.prof[text] = count
        
    def iterate(self):
        #self.logger.debug('%s iterate' % type(self).__name__)
        if self.profile:
            self.profile_update('buttons')
        before = time.time()
        btnmask = self.read_buttons()
        for btn in xrange(len(buttons)):
            if not self.update_button(btnmask,btn):
                self.logger.debug("Got exit from button %d" % btn)
                return False
        
        if self.iterate_timeout():
            if self.autochange_real > 0:
                self.iterate_autocounter()
        
            if self.do_init:
                self.init_printer()
                self.updatecounter = 0
            
            if self.updatecounter == 0:
                if self.profile:
                    self.profile_update('display')
                if not self.printers[self.idx].iterate():
                    self.logger.debug("Got exit from printer %d" % self.idx)
                    return False
            self.updatecounter = (self.updatecounter+1)%self.iteratediv
            
        after = time.time()
        dt = after-before
        if dt < self.ticklength:
            time.sleep(self.ticklength-dt)

        return True
