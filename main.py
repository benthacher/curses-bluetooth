#!/usr/bin/env python3

import sys, os
import curses

from cdom import CDOM, CDOMStyle
from element import Link
from event import Event, KeyEvent

import pages

from enum import Enum

def draw_menu(stdscr):
    k = -1
    
    stdscr.clear()
    stdscr.refresh()

    stdscr.nodelay(1)

    curses.curs_set(0)

    curses.mousemask(1)

    cdom = CDOM(stdscr,
        style=CDOMStyle(
            backgroundColor  = (curses.COLOR_CYAN,  curses.COLOR_CYAN),
            titleColor       = (curses.COLOR_RED,   curses.COLOR_MAGENTA),
            textColor        = (curses.COLOR_BLACK, curses.COLOR_WHITE),
            highlightedColor = (curses.COLOR_WHITE, curses.COLOR_YELLOW),
            wallColor        = (curses.COLOR_BLACK, curses.COLOR_MAGENTA),
            shadowColor      = (curses.COLOR_BLACK, curses.COLOR_CYAN)
        )
    )

    cdom.addPages(*pages.pages)

    cdom.goHome()

    while True:

        k = stdscr.getch()

        height, width = stdscr.getmaxyx()

        highlighted = cdom.currentPage.highlightedElement

        if k != -1:
            # if no highlighted element, nothing below matters
            if not highlighted:
                continue

            # make key event with k
            e = KeyEvent(k)

            # if element has a custom onkey function, run it with e
            if highlighted.onkey:
                highlighted.onkey(highlighted, e)
            
            if hasattr(highlighted, 'defaultOnkey'):
                highlighted.defaultOnkey(e)

            # if e.preventDefault has been called, prevent default
            if e.canceled:
                continue

            if k == curses.KEY_LEFT:
                if cdom.history:
                    cdom.goToPage(cdom.history.pop(), True)

            # default key events
            if k == curses.KEY_UP:
                cdom.currentPage.selectPrevious()
            elif k == curses.KEY_DOWN:
                cdom.currentPage.selectNext()
            elif KeyEvent.isEnter(k) or (k == curses.KEY_RIGHT and isinstance(highlighted, Link)):
                if isinstance(highlighted, Link):
                    cdom.goToPage(highlighted.url)
                
                if highlighted.onselect:
                    e = Event()

                    highlighted.onselect(highlighted, e)

                    if not e.canceled and hasattr(highlighted, 'defaultOnselect'):
                        highlighted.defaultOnselect()

                elif hasattr(highlighted, 'defaultOnselect'):
                    highlighted.defaultOnselect()

        cdom.renderPage(cdom.currentPage, height, width)

        curses.delay_output(16)

def main():
    curses.wrapper(draw_menu)

if __name__ == '__main__':
    os.system('cat ~/.cache/wal/sequences')
    main()
