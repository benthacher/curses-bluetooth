import curses

from copy import deepcopy
from enum import Enum

class Align(Enum):
    LEFT   = 0
    CENTER = 1
    RIGHT  = 2

class Style:
    def __init__(self, color = None, align: Align = Align.LEFT, weight = curses.A_NORMAL, indent: int = 0, display = True, height = None, displayIndex: int = 0):
        self.color = color
        self.align = align
        self.weight = weight
        self.indent = indent
        self.display = display
        self.height = height
        self.displayIndex = displayIndex

class Element:
    def __init__(self, text: str = '', style: Style = Style(), ID: str = '', classList: list = [], data: dict = {}, onrefresh = None, onload = None, onunload = None):
        self.text = text
        self.style = style
        self.ID = ID
        self.classList = classList
        self.onload = onload
        self.onunload = onunload
        self.onrefresh = onrefresh
        self.page = None

        self.data = data
    
    def copy(self):
        return Element(
            text=self.text[:],
            style=deepcopy(self.style),
            ID=self.ID[:],
            classList=self.classList[:],
            data=deepcopy(self.data),
            onload=self.onload,
            onunload=self.onunload,
            onrefresh=self.onrefresh
        )

    def index(self):
        return self.page.elements.index(self)
    
    def lines(self):
        lines = self.text.split('\n')[self.style.displayIndex:]

        if self.style.height:
            if len(lines) > self.style.height:
                lines = lines[:self.style.height]
            else:
                lines.extend([''] * max(0, self.style.height - len(lines)))

        return lines
    
    def getText(self):
        return [
            ' ' * self.style.indent + self.text,
            self.text,
            self.text + ' ' * self.style.indent
        ][self.style.align.value]

    def displayHeight(self):
        return self.style.height or len(self.lines())

    def displayWidth(self):
        return len(self.getText())

class Break(Element):
    def __init__(self, ID: str = ''):
        super().__init__(ID=ID)

    def copy(self):
        return Break(ID=self.ID[:])

class Linebreak(Element):
    def __init__(self, char: str = '━', ID: str = ''):
        super().__init__(ID=ID)

        self.char = char

    def defaultOnrefresh(self):
        self.text = (self.page.displaySize[1] - 2) * self.char

    def copy(self):
        return Linebreak(ID=self.ID[:], char=self.char[:])

class Wallbreak(Linebreak):
    def __init__(self, ID: str = ''):
        super().__init__(ID=ID, char='═')

    def copy(self):
        return Wallbreak(ID=self.ID[:])

class ThinWallbreak(Linebreak):
    def __init__(self, ID: str = ''):
        super().__init__(ID=ID, char='─')

    def copy(self):
        return ThinWallbreak(ID=self.ID[:])

class Selectable(Element):
    def __init__(self, text: str = '', style: Style = Style(), ID: str = '', classList: list = [], data: dict = {}, onrefresh = None, onload = None, onunload = None, onkey = None, onselect = None):
        super().__init__(text, style, ID, classList, data, onrefresh, onload, onunload)

        self.onkey = onkey
        self.onselect = onselect
    
    def copy(self):
        return Selectable(
            text=self.text[:],
            style=deepcopy(self.style),
            ID=self.ID[:],
            classList=self.classList[:],
            data=deepcopy(self.data),
            onload=self.onload,
            onunload=self.onunload,
            onkey=self.onkey,
            onrefresh=self.onrefresh,
            onselect=self.onselect
        )
    
class Link(Selectable):
    def __init__(self, label: str = '', style: Style = Style(), ID: str = '', classList: list = [], data: dict = {}, onrefresh = None, onload = None, onunload = None, onkey = None, onselect = None, url: str = ''):
        super().__init__('', style, ID, classList, data, onrefresh, onload, onunload, onkey, onselect)

        self.label = label
        self.url = url

    def copy(self):
        return Link(
            label=self.label[:],
            style=deepcopy(self.style),
            ID=self.ID[:],
            classList=self.classList[:],
            data=deepcopy(self.data),
            onload=self.onload,
            onunload=self.onunload,
            onkey=self.onkey,
            onrefresh=self.onrefresh,
            onselect=self.onselect,
            url=self.url[:]
        )

    def defaultOnload(self):
        self.updateText()

    def updateText(self):
        self.text = self.label + ' → '

class Input(Selectable):
    def __init__(self, text: str = '', style: Style = Style(), ID: str = '', classList: list = [], data: dict = {}, onrefresh = None, onload = None, onunload = None, onkey = None, onselect = None, value = '', label = '', boxed = True, selected = False):
        super().__init__(text, style, ID, classList, data, onrefresh, onload, onunload, onkey, onselect)

        self.selected = selected
        self.value = value
        self.label = label
        self.boxed = boxed
        self.onrefresh = onrefresh
        self.onkey = onkey

    def copy(self):
        return Input(
            text=self.text[:],
            style=deepcopy(self.style),
            ID=self.ID[:],
            classList=self.classList[:],
            data=deepcopy(self.data),
            onload=self.onload,
            onunload=self.onunload,
            onkey=self.onkey,
            onrefresh=self.onrefresh,
            onselect=self.onselect,
            value=self.value[:] if type(self.value) is str else self.value,
            label=self.label[:],
            boxed=self.boxed,
            selected=self.selected
        )

    def defaultOnrefresh(self):
        self.updateText()

        if self.selected:
            self.style.weight = curses.A_UNDERLINE
        else:
            self.style.weight = curses.A_NORMAL

    def defaultOnkey(self, e):
        k = e.key

        if self.selected:
            char = curses.keyname(k).decode('utf-8')

            # e.preventDefault()

            if len(char) == 1:
                self.value += char

            if k == curses.KEY_BACKSPACE:
                self.value = self.value[:-1]
            elif k == 27:
                self.selected = False
        
        if k == curses.KEY_ENTER or k == 10 or k == 13:
            self.selected = not self.selected

        self.updateText()
    
    def updateText(self):
        self.text = f"{self.label}{': ' * (self.label != '')}{'[' * self.boxed}{self.value}{']' * self.boxed}"

class Dropdown(Input):
    def __init__(self, text: str = '', style: Style = Style(), ID: str = '', classList: list = [], data: dict = {}, onrefresh = None, onload = None, onunload = None, onkey = None, onselect = None, value = '', label = '', boxed = True, valueList=[]):
        super().__init__(text, style, ID, classList, data, onrefresh, onload, onunload, onkey, onselect, value, label, boxed)

        if value == '':
            self.value = valueList[0]
        
        self.valueList = valueList
        self.onkey = onkey

    def copy(self):
        return Dropdown(
            text=self.text[:],
            style=deepcopy(self.style),
            ID=self.ID[:],
            classList=self.classList[:],
            data=deepcopy(self.data),
            onload=self.onload,
            onunload=self.onunload,
            onkey=self.onkey,
            onrefresh=self.onrefresh,
            onselect=self.onselect,
            value=self.value[:] if type(self.value) is str else self.value,
            label=self.label[:],
            boxed=self.boxed,
            valueList=self.valueList[:]
        )

    def defaultOnkey(self, e):
        k = e.key

        if self.selected:
            e.preventDefault()

            if k == curses.KEY_DOWN:
                i = self.valueList.index(self.value)

                if i == len(self.valueList) - 1:
                    i = -1
                
                self.value = self.valueList[i + 1]
            elif k == curses.KEY_UP:
                i = self.valueList.index(self.value)

                if i == 0:
                    i = len(self.valueList)
                
                self.value = self.valueList[i - 1]
            elif k == 27:
                self.selected = False
        
        if k == curses.KEY_ENTER or k == 10 or k == 13:
            self.selected = not self.selected

        self.updateText()

class Checkbox(Selectable):
    def __init__(self, label: str = '', style: Style = Style(), ID: str = '', classList: list = [], data: dict = {}, onrefresh = None, onload = None, onunload = None, onkey = None, onselect = None, checked = False):
        super().__init__('', style, ID, classList, data, onrefresh, onload, onunload, onkey, onselect)

        self.checked = checked
        self.label = label
        
        self.onselect = onselect

        self.updateText()

    def defaultOnselect(self):
        self.checked = not self.checked

        self.updateText()
    
    def copy(self):
        return Checkbox(
            label=self.label[:],
            style=deepcopy(self.style),
            ID=self.ID[:],
            classList=self.classList[:],
            data = deepcopy(self.data),
            onrefresh=self.onrefresh,
            onload=self.onload,
            onunload=self.onunload,
            onkey=self.onkey,
            onselect=self.onselect,
            checked=self.checked
        )

    def updateText(self):
        self.text = f"{self.label}: [{'✓' if self.checked else ' '}]"
