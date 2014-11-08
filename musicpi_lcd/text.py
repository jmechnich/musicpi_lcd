class Page(object):
    def __init__(self, cols=16, rows=2):
        self.cols = cols
        self.rows = rows
        self.items = []
        self.pos = 0
    
    def pos_col(self):
        return self.pos%self.cols

    def pos_row(self):
        return self.pos/self.cols
    
    def add(self, text):
        if self.pos >= self.cols*self.rows:
            print "Warning: position larger than page size"
            print self.pos_col(), self.pos_row(), text.__dict__
        self.items += [ (self.pos, text) ]
        #print "Adding new item at", self.pos_col(), self.pos_row(), text
        self.pos += text.width

    def newline(self):
        col = self.pos_col()
        if col == 0:
            return
        self.pos = self.pos + self.cols-col
    
    def render(self, force=False, set_cursor_func=None, message_func=None):
        for pos, text in self.items:
            self.pos = pos
            if set_cursor_func:
                #print "Moving cursor to", self.pos_col(),self.pos_row()
                set_cursor_func(self.pos_col(),self.pos_row())
            if message_func and (text.update() or force):
                #print "Rendering '%s'" % str(text)
                message_func( str(text))

    def add_line(self,text,header=None):
        width = self.cols
        if header:
            headertext = Text(header+" ") 
            self.add(headertext)
            width -= headertext.width
        text.width = width
        self.add(text)

    def add_scroll_line(self,rawtext,header=None):
        width = self.cols
        if header:
            headertext = Text(header+" ") 
            self.add(headertext)
            width -= headertext.width
        self.add(ScrollText(rawtext,width))

class Text(object):
    def __init__(self, text="", width=-1):
        self.text  = text
        if width < 0:
            width = len(self.text)
        self.width = width
        self.changed = True
    def __str__(self):
        return self.text[:self.width].ljust(self.width)

    def setText(self,text):
        self.text = text
        self.changed = True
        
    def update(self):
        ret = self.changed
        if self.changed:
            self.changed = False
        return ret
    
class CycleText(Text):
    def __init__(self, textlist=[], width=-1,initial=0, delay=2):
        self.textlist = textlist
        self.counter  = initial
        self.delay    = delay
        self.delaycounter = 0
        if width < 0:
            width = len(max(self.textlist,key=len))
        
        if len(self.textlist) > initial and len(self.textlist[initial]):
            text = self.textlist[initial]
        else:
            text = ''
        super(CycleText,self).__init__(text,width)
 
    def setList(self,textlist):
        self.textlist = textlist
        if not self.counter < len(self.textlist):
            self.counter = 0
        self.delaycounter = 0
        
    def update(self):
        self.delaycounter = (self.delaycounter+1)%self.delay
        if self.delaycounter == 1:
            if len(self.textlist):
                self.counter = (self.counter+1)%len(self.textlist)
                self.text = self.textlist[self.counter].ljust(self.width)
            return True
        return False


class ScrollText(Text):
    def __init__(self,scrolltext="",width=-1,wait=1,inc=1):
        self.wait = wait
        self.inc  = inc
        if width < 0: width = len(scrolltext)
        super(ScrollText,self).__init__(width=width)
        self.setText(scrolltext)
    
    def setText(self, text):
        self.scrolltext = text
        dx = max(0,len(self.scrolltext)-self.width)
        self.loop    = [0]*self.wait + [self.inc]*dx + [0]*self.wait + [-self.inc]*dx
        self.counter = 0
        self.looppos = 0
        
    def update(self):
        self.text = self.scrolltext[self.looppos:self.looppos+self.width].ljust(self.width)
        self.looppos += self.loop[self.counter]
        self.counter = (self.counter+1)%len(self.loop)
        return True
