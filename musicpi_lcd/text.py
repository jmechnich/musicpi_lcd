class ScrollText(object):
    def __init__(self,text,maxw):
        self.text    = text
        self.maxw    = maxw
        self.pos     = 0
        self.counter = 0
        self.wait    = 5
        self.inc     = 1
    
    def next(self):
        if len(self.text) > self.maxw:
            end = self.pos+self.maxw
            if end == len(self.text):
                if self.counter == 0:
                    self.counter = self.wait
                elif self.counter == 1:
                    self.inc = -1
                    self.pos += self.inc
                    end += self.inc
                self.counter -= 1
                return self.text[self.pos:end]
            elif self.pos == 0:
                if self.counter == 0:
                    self.counter = self.wait
                elif self.counter == 1:
                    self.inc = 1
                    self.pos += self.inc
                    end += self.inc
                self.counter -= 1
                return self.text[self.pos:end]
            else:
                self.pos += self.inc
                end += self.inc
                
            return self.text[self.pos:end]
        else:
            return self.text
