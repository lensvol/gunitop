#coding: utf-8

import curses

from itertools import count

COLUMN_PADDING = 1

def animation(frames):
    def player():
        while True:
            for frame in frames:
                yield frame
    return player().next


class TabularWindow(object):
    vlines = []
    hlines = []
    title = None
    foreground = curses.COLOR_WHITE
    background = curses.COLOR_BLACK
    closing = False
    refresh_delay = 100 # in milliseconds

    taskbar = []
    columns = []
    texts = []

    start_row = 0

    def init_window(self):
        my, mx = self.win.getmaxyx()
        x = 0
        for header, width in self.columns:
            if width == -1:
                width = mx - x - 4
            self.texts.append((x + 1 + COLUMN_PADDING, 1, header.center(width)))
            x += width + (COLUMN_PADDING * 2) + 1
            if mx <= x + 4:
                break
            self.vlines.append(x)
        self.hlines.append(2)

    def _display_taskbar(self):
        win = self.win
        my, mx = win.getmaxyx()
        # Trying to acquire contents of taskbar
        contents = map(lambda el: callable(el) and el() or el, self.taskbar)

        if contents:
            # Because we align taskbar contents to the right corner, we need to reverse them
            contents = reversed(filter(lambda x: x, contents))
            y = my - 1
            x = mx - 3
            for el in contents:
                if isinstance(el, tuple):
                    text, attr = el
                else:
                    text = el
                    attr = curses.A_NORMAL | curses.color_pair(1)
                # Draw the layout
                win.addch(y, x - 1, ' ')
                win.addch(y, x, curses.ACS_VLINE)
                x -= len(text) + 3
                if x > 3:
                    win.addch(y, x, curses.ACS_RTEE)
                    win.addch(y, x + 1, ' ')
                    win.addstr(y, x + 2, text, attr)
                win.addch(y, mx - 3, curses.ACS_LTEE)

    def _display_rows(self):
        win = self.win
        my, mx = win.getmaxyx()
        y = count(3).next
        height = my - 5
        start = self.start_row
        rows = self.get_rows()
        total = len(rows)

        if start >= total:
            start = total - my
        if start < 0:
            start = 0

        for row in rows:
            line = y()
            x = 1 + COLUMN_PADDING
            if line >= height:
                break
            for (i, (_, width)) in enumerate(self.columns):
                text = unicode(row[i])
                if width == -1:
                    width = mx - x - COLUMN_PADDING - 2
                    text = text.ljust(width)
                else:
                    text = text.center(width)
                win.addstr(line, x, text[:width], curses.color_pair(1))
                x += width + (COLUMN_PADDING * 2) + 1

    def get_rows(self):
        return []

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

        for (x, y, text) in self.texts:
            win.addstr(y, x, text, curses.A_NORMAL)

        self._draw_title()
        self._display_taskbar()
        self._display_rows()

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


class TestTabWindow(TabularWindow):
    taskbar = [
        animation(['*--', '-*-', '--*']),
        animation('0123456789'),
        ('Hello there!', curses.A_BOLD)
    ]

    columns = [
        ("PID", 5),
        ("CPU", 5),
        ("MEMORY", 8),
        ("STATUS", -1)
    ]

    def get_rows(self):
        return [['65535', '200%', '1024MB', '4'*100]]
