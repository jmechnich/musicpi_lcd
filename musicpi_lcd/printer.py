import Adafruit_CharLCD as LCD

class Printer(object):
    def __init__(self,**kwargs):
        self.delay = 0.3        
        self.__dict__.update(kwargs)
        
        self.rowtext = []
        self.rowidx = 0
        self.tickcounter = 0

    def iterate(self):
        if self.tickcounter == 0:
            for row in xrange(self.rows):
                actualrow = self.rowidx + row
                if actualrow < len(self.rowtext) and self.rowtext[actualrow]:
                    t = self.rowtext[actualrow] 
                    self.lcd.set_cursor(self.cols-t.maxw,row)
                    self.lcd.message(t.next().ljust(t.maxw))
                else:
                    self.lcd.set_cursor(0,row)
                    self.lcd.message("".ljust(self.cols))
        self.tickcounter += self.ticklength
        if self.tickcounter > self.delay:
            self.tickcounter = 0

    def button_pressed(self,btn):
        if btn == LCD.RIGHT:
            self.next_page()
        elif btn == LCD.DOWN:
            self.scroll( 1)
        elif btn == LCD.UP:
            self.scroll(-1)
        elif btn == LCD.LEFT:
            self.prev_page()
            
    def prev_page(self):
        self.rowidx -= 2
        if self.rowidx < 0:
            self.rowidx = 0

    def next_page(self):
        self.rowidx += 2
        if self.rowidx >= len(self.rowtext):
            self.rowidx = 0

    def scroll(self,ds):
        self.rowidx += ds
        if self.rowidx >= len(self.rowtext)-1:
            self.rowidx = len(self.rowtext)-2
        if self.rowidx < 0:
            self.rowidx = 0
