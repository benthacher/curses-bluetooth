from cdom import CDOM
from element import Selectable, Link

from copy import deepcopy

class PageStyle():
    def __init__(self, border = True, margin = (1, 1), shadow = True):
        self.border = border
        self.margin = margin
        self.shadow = shadow

class Page:
    def __init__(self, url: str, title: str, elements: list, size: tuple = (None, None), style: PageStyle = PageStyle(), data: dict = {}, stateless = True, onload = None, onunload = None, onrefresh = None):
        self.url = url
        self.title = title
        self.size = size
        self.displaySize = (0, 0)
        self.style = style
        self.elements = elements
        self.data = data
        self.stateless = stateless
        self.onload = onload
        self.onunload = onunload
        self.onrefresh = onrefresh

        self.highlightedElement = None
        self.selectNext()

    def copy(self):
        cp = Page(
            url=self.url[:],
            title=self.title[:],
            size=self.size + tuple(),
            style=deepcopy(self.style),
            elements=[elem.copy() for elem in self.elements],
            data=deepcopy(self.data),
            stateless=self.stateless,
            onload=self.onload,
            onunload=self.onunload,
            onrefresh=self.onrefresh
        )

        cp.setCDOM(self.cdom)

        return cp

    def setCDOM(self, cdom: CDOM):
        self.cdom = cdom

        for element in self.elements:
            element.cdom = cdom
            element.page = self
    
    def selectPrevious(self):
        start = 0 if self.highlightedElement is None else (self.elements.index(self.highlightedElement) - 1)
        length = len(self.elements)

        for i in range(start + length, start, -1):
            i %= length
            elem = self.elements[i]

            if isinstance(elem, Selectable) and elem.style.display:
                self.highlightedElement = self.elements[i]
                return
        
        self.highlightedElement = None

    def selectNext(self):
        start = 0 if self.highlightedElement is None else (self.elements.index(self.highlightedElement) + 1)
        length = len(self.elements)

        for i in range(start, start + length):
            i %= length
            elem = self.elements[i]

            if isinstance(elem, Selectable) and elem.style.display:
                self.highlightedElement = self.elements[i]
                return

        self.highlightedElement = None

    def getElementByID(self, ID: str):
        for elem in self.elements:
            if elem.ID == ID:
                return elem
        
    def getElementsByClassName(self, className: str):
        res = []

        for element in self.elements:
            if className in element.classList:
                res.append(element)

        return res
    
    def addElements(self, elements: list, index: int = -1):
        if index == -1:
            index = len(self.elements)
        
        for element in elements:
            element.cdom = self.cdom
            element.page = self

            self.elements.insert(index, element)
            index += 1

            if element.onload is not None:
                element.onload(element)

    def addElement(self, element, index: int = -1):
        self.addElements([ element ], index)
    
    def removeElements(self, elements):
        for element in elements:
            self.removeElement(element)
    
    def removeElement(self, element):
        if element is self.highlightedElement:
            self.selectPrevious()

        self.elements.remove(element)
