import curses

class Event():
    def __init__(self):
        self.canceled = False

    def preventDefault(self):
        self.canceled = True

class KeyEvent(Event):
    def __init__(self, key):
        super().__init__()

        self.key = key
    
    @staticmethod
    def isEnter(key):
        return (key == curses.KEY_ENTER or key == 10 or key == 13)