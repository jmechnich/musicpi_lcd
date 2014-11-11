from musicpi_lcd.lcd  import LCD, buttons, colors
from musicpi_lcd.text import *

class Printer(object):
    def __init__(self,**kwargs):
        # configurable variables
        self.color = colors['white']
        self.splashticks = 1

        self.__dict__.update(kwargs)
        
        self.init_layout()

    def init_layout(self):
        self.pages = []
        self.active = -1
        self.btncounter = dict(zip(buttons,[0]*len(buttons)))
        self.longpress = 3
        self.splash = None
        self.splashcounter = 0
        
    # main loop function
    def iterate(self):
        #if self.debug: print type(self).__name__, 'iterate'
        self.render()
            
    # display functions
    def render(self,force=False):
        #if self.debug: print type(self).__name__ + " render", force
        if self.splashcounter > 0:
            self.splashcounter -= 1
            return
        if self.splash:
            if self.debug: print type(self).__name__ + " hiding splash"
            self.splash = None
            force = True
        if (self.active < 0) or (self.active >= len(self.pages)):
            return
        self.render_page( self.pages[self.active], force=force)

    def render_page(self, page, force=False):
        page.render(force=force)

    # default button handlers
    def button_released(self,btn):
        pass
    
    def button_pressed(self,btn,repeat):
        pass
          
    def button_pressed_long(self,btn):
        pass
            
    def button_clicked(self,btn):
        if btn == LCD.SELECT:
            self.next_page()
    
    # default actions
    def show_splash(self,text,timeout=-1):
        self.splash = Page(self.lcd)
        words = text.split('\n')
        firstline  =  text.center(self.cols)
        secondline = ''
        if len(words) > 1:
            firstline  = ''.join(words[:len(words)/2]).center(self.cols)
            secondline = ''.join(words[len(words)/2:]).center(self.cols)
        self.splash.add(ScrollText(firstline,  width=self.cols))
        self.splash.add(ScrollText(secondline, width=self.cols))
        self.splashcounter = self.splashticks if timeout < 0 else timeout
        self.render_page(self.splash, force=True)
    
    def stop(self):
        pass
    
    def set_background(self):
        self.lcd.set_color(*self.color)
    
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
