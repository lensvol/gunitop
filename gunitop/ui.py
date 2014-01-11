#coding: utf-8

import curses


class TabularWindow(object):
    vlines = []
    hlines = []
    title = None
    foreground = curses.COLOR_WHITE
    background = curses.COLOR_BLACK
    closing = False
    refresh_delay = 100 # in milliseconds

    def handle_keypress(self):
        try:
            key = self.win.getkey().upper()
        except:
            return
        if key == 'Q':
            self.closing = True

    def _draw_title(self):
        if self.title:
            title = self.title
            win = self.win
            mx = self.screen_width
            padding = (mx - len(title)) / 2 - 4
            win.addch(0, padding + 1, curses.ACS_RTEE)
            win.addstr(0, padding + 2, ''.join([' ', title, ' ']), curses.color_pair(1))
            win.addch(0, padding + len(title) + 4, curses.ACS_LTEE)

    def init_screen(self):
        self.win = curses.initscr()
        self.win.nodelay(True)
        self.win.keypad(True)
        curses.start_color()

        # Setting transparency and default color pair
        curses.use_default_colors()
        curses.init_pair(1, self.foreground, self.background)

        # Hiding cursor
	curses.curs_set(0)
        curses.cbreak()
        self.init_window()

    def resetscreen(self):
        curses.nocbreak()
        self.win.keypad(False)
	curses.curs_set(1)
        curses.echo()
        curses.endwin()

    def draw(self):
        self.handle_keypress()

        win = self.win
        my, mx = win.getmaxyx()

        win.erase()
        win.bkgd(' ', curses.color_pair(1))
        win.border()

        # Draw horizontal lines and intersections with border
        for x in self.vlines:
            win.vline(1, x, curses.ACS_VLINE, self.screen_height - 2)
            win.addch(0, x, curses.ACS_TTEE)
            win.addch(my - 1, x, curses.ACS_BTEE)

        for y in self.hlines:
            win.hline(y, 1, curses.ACS_HLINE, self.screen_width - 2)
            win.addch(y, 0, curses.ACS_LTEE)
            win.addch(y, mx - 1, curses.ACS_RTEE)
            # Draw intersections with vertical lines
            for x in self.vlines:
                win.addch(y, x, curses.ACS_PLUS)

        self._draw_title()

        win.refresh()

    def nap(self):
        curses.napms(self.refresh_delay)

    @property
    def screen_width(self):
        _, mx = self.win.getmaxyx()
        return mx

    @property
    def screen_height(self):
        my, _ = self.win.getmaxyx()
        return my

    @property
    def display_width(self):
        _, mx = self.win.getmaxyx()
        return mx - BORDER_SPACING

    @property
    def display_height(self):
        my, _ = self.win.getmaxyx()
        return my - 7
