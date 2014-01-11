#coding: utf-8

import curses
import collections
import json
import socket
import sys
import threading
import time

# for keeping track of y line offsets
from itertools import count

from ui import TabularWindow, animation, TestTabWindow

workers = {}
# In seconds
PERIOD = 1
LEFT_BORDER_OFFSET = 3
BORDER_SPACING = 1

class MonitorWindow(object):
    win = None
    closing = False
    screen_delay = PERIOD
    foreground = curses.COLOR_GREEN
    background = -1
    spinner = animation('|/-\\')

    def __init__(self, workers):
        self.workers = workers

    def handle_keypress(self):
        try:
            key = self.win.getkey().upper()
        except:
            return

        if key == 'Q':
            self.closing = True

    def draw_spinner(self):
        '''
        Draw simple heartbeat indicator, which will loop through specified frames
        in bottom right corner.
        '''
        win = self.win
        mx, my = self.screen_width, self.screen_height
        # Get next frame
        frame = self.spinner()
        x = mx - len(frame) - 10

        # Draw boundaries and the frame
        win.addch(my - 1, x, curses.ACS_RTEE)
        win.addstr(my - 1, x + 1, ''.join([' ', frame, ' ']), curses.color_pair(1))
        win.addch(my - 1, x + len(frame) + 3, curses.ACS_LTEE)

    def draw(self):
        win = self.win
        self.handle_keypress()
        x = LEFT_BORDER_OFFSET
        blank_line = y = count(1).next
        mx, my = win.getmaxyx()
        win.erase()
        win.bkgd(' ', curses.color_pair(1))
        win.border()
        win.addstr(y(), x,
                   '   '.join(['PID'.center(6), 'STATUS', '']),
                   curses.color_pair(1))

        for pid, w in self.workers.iteritems():
            win.addstr(y(), x,
                       '   '.join([str(pid).center(6), w['status'].center(6), w['text'][:mx-x-6]]),
                       curses.A_NORMAL)

        win.hline(2, 1, curses.ACS_HLINE, self.screen_width - 2)
        win.vline(1, x + 7, curses.ACS_VLINE, self.screen_height - 2)
        win.vline(1, x + 16, curses.ACS_VLINE, self.screen_height - 2)

        # Painting intersections...
	win.addch(2, 0, curses.ACS_LTEE)
	win.addch(2, self.screen_width - 1, curses.ACS_RTEE)
        win.addch(2, x + 7, curses.ACS_PLUS)

	win.addch(0, x + 7, curses.ACS_TTEE)
	win.addch(self.screen_height - 1, x + 7, curses.ACS_BTEE)

	win.addch(0, x + 16, curses.ACS_TTEE)
	win.addch(self.screen_height - 1, x + 16, curses.ACS_BTEE)
        win.addch(2, x + 16, curses.ACS_PLUS)

        self.draw_spinner()
        win.refresh()
        self.evict_workers()

    def init_screen(self):
        self.win = curses.initscr()
        self.win.nodelay(True)
        self.win.keypad(True)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, self.foreground, self.background)
	curses.curs_set(0)
        curses.cbreak()

    def evict_workers(self):
        for pid, worker in workers.items():
            if worker['status'] == 'EXIT':
                workers.pop(pid)

    def resetscreen(self):
        curses.nocbreak()
        self.win.keypad(False)
	curses.curs_set(1)
        curses.echo()
        curses.endwin()

    def nap(self):
        curses.napms(self.screen_delay * 100)

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

class ListenerThread(threading.Thread):

    def __init__(self, workers, host="localhost", port=18114):
        self.workers = workers
        self.stop = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        host = socket.gethostbyname(host)
        self.socket.bind((host, port))
        self.socket.setblocking(False)
        threading.Thread.__init__(self)

    def process(self, text):
        info = json.loads(text)
        info_type = info['type']
        pid = info['worker']['pid']
        worker = self.workers.setdefault(pid, {
            'ppid': -1,
            'text': u'Waiting...',
            'status': 'IDLE',
            'statistics': collections.Counter()
        })

        if info_type == 'spawn':
            worker['ppid'] = info['worker']['ppid']
        elif info_type == 'request':
            worker['text'] = '{0} {1}'.format(info['method'], info['path'])
            worker['status'] = 'WORK'
        elif info_type == 'response':
            worker['text'] = 'Waiting...'
            worker['statistics'][info['status_code']] += 1
            worker['status'] = 'IDLE'
        elif info_type == 'exit':
            worker['status'] = 'EXIT'
            worker['text'] = 'SIGINT / SIGTERM / SIGQUIT'

    def run(self):
        while not self.stop:
            try:
                text, source = self.socket.recvfrom(8192)
            except:
                time.sleep(PERIOD)
            else:
                self.process(text)
            #time.sleep(PERIOD)

def main():
    listener = ListenerThread(workers)
    listener.start()

    #import locale
    #locale.setlocale(locale.LC_ALL, '')

    try:
        monitor = MonitorWindow(workers)
        monitor.init_screen()
        while not monitor.closing:
            monitor.draw()
            monitor.nap()
        monitor.resetscreen()
    except (KeyboardInterrupt, SystemExit):
        pass

    print 'Waiting for listener to stop...'
    listener.stop = True
    listener.join()
