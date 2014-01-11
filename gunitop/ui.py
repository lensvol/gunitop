#coding: utf-8

import curses

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

    def init_window(self):
        my, mx = self.win.getmaxyx()
        x = 1
        for header, width in self.columns:
            if width == -1:
                width = mx - x - 4
            self.texts.append(
                (x+1, 1, header.center(width))
            )
            x += width + (COLUMN_PADDING * 2)
            if mx <= x + 4:
                break
            self.vlines.append(x)
        self.hlines.append(2)

    def _display_taskbar(self):
        win = self.win
        my = self.screen_height - 1

        contents = map(lambda el: callable(el) and el() or el, self.taskbar)
        contents = filter(lambda x: x, contents)

        total_len = ((len(contents) - 1) * 3) + reduce(lambda t,s: t + len(s), contents, 0)
        padding = ((self.screen_width - total_len) / 2) - 1
        win.addstr(my, padding, ' | '.join(contents), curses.color_pair(1))

        win.addch(my, padding + total_len, ' ')
        win.addch(my, padding + total_len + 1, curses.ACS_LTEE)
        win.addch(my, padding - 1, ' ')
        win.addch(my, padding - 2, curses.ACS_RTEE)

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
        'Hello there!'
    ]

    columns = [
        ("PID", 5),
        ("CPU", 5),
        ("MEMORY", 8),
        ("STATUS", -1)
    ]
