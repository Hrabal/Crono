
import operator
from functools import reduce
from datetime import datetime, timedelta
from collections import Counter
from inspect import getmembers, ismethod

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class CronoEvent:
    event_count = Counter()
    event_own_dur = Counter()
    event_dur = Counter()
    cumulative_duration = Counter()
    cumulative_own_duration = Counter()

    def __init__(self, agent, event_id, breakpoint=False):
        self.agent = agent
        self.event_count[self.agent] += 1
        self.start_t = self.stop_t = self.parent = None
        self.childs = []
        self.event_id = event_id
        self.parent = None
        self.is_breakpoint = breakpoint

    def start(self):
        self.start_t = datetime.now()

    def stop(self):
        self.stop_t = datetime.now()
        own = self.own_duration.total_seconds()
        dur = self.duration.total_seconds()
        self.event_own_dur[self.event_id] += own
        self.event_dur[self.event_id] += dur
        self.cumulative_duration[self.agent] += dur
        self.cumulative_own_duration[self.agent] += own

    @property
    def duration(self):
        return self.stop_t - self.start_t

    @property
    def childs_duation(self):
        return sum([c.duration for c in self.childs], timedelta())

    @property
    def own_duration(self):
        return self.duration - self.childs_duation

    def _set_child(self, child):
        self.childs.append(child)
        child.parent = self

    @property
    def depth(self):
        return 0 if not self.parent else self.parent.depth + 1

    def __repr__(self):
        eid = str(self.event_id).ljust(3 ,' ')
        name = str(self.agent.__name__ if not self.is_breakpoint else self.agent).ljust(60-(self.depth*2), " ")
        depth = '  ' * self.depth
        count = self.event_count[self.agent]
        commons = [a[0] for a in self.event_count.most_common(2)]
        count_color = bcolors.FAIL if not self.is_breakpoint and self.agent in commons else ''

        most_durations = [a[0] for a in self.event_dur.most_common(2)]
        dur_color = bcolors.FAIL if self.event_id in most_durations else ''

        most_own_durations = [a[0] for a in self.event_own_dur.most_common(2)]
        own_dur_color = bcolors.FAIL if self.event_id in most_own_durations else ''

        cum_duration = self.cumulative_duration[self.agent]
        most_cum_dur = [a[0] for a in self.cumulative_duration.most_common(2)]
        cum_duration_color = bcolors.FAIL if self.agent in most_cum_dur else ''

        cum_own_duration = self.cumulative_own_duration[self.agent]
        most_cum_own_dur = [a[0] for a in self.cumulative_own_duration.most_common(2)]
        cum_own_duration_color = bcolors.FAIL if self.agent in most_cum_own_dur else ''
        return '\n'.join([
            f'#{eid}|{depth}{count_color}{name}{bcolors.ENDC} - {dur_color}{self.duration.total_seconds():08.4f}{bcolors.ENDC} - {own_dur_color}{self.own_duration.total_seconds():08.4f}{bcolors.ENDC} | {count_color}{count:02}{bcolors.ENDC} {cum_duration_color}{cum_duration:08.4f}{bcolors.ENDC} - {cum_own_duration_color}{cum_own_duration:08.4f}{bcolors.ENDC}'
        ] + [str(child) for child in self.childs])


class Crono:

    def __init__(self):
        self.events = []
        self.curr_event = None
        self.event_count = 0

    def _add_event(self, method, breakpoint=False):
        self.event_count += 1
        event = CronoEvent(method, self.event_count, breakpoint=breakpoint)
        if self.curr_event:
            if self.curr_event.is_breakpoint:
                self._stop_event(self.curr_event)
            if self.curr_event:
                self.curr_event._set_child(event)
        else:
            self.events.append(event)
        self.curr_event = event
        event.start()
        return event

    def _stop_event(self, event):
        event.stop()
        self.curr_event = event.parent or None

    def _cronize(self, method):
        def wrapper(*args, **kwargs):
            event = self._add_event(method)
            ret = method(*args, **kwargs)
            self._stop_event(event)
            return ret
        return wrapper

    def track(self, cls):
        def decorate(cls):
            for method in dir(cls):
                if not method[:2] == '__' and callable(getattr(cls, method)):
                    setattr(cls, method, self._cronize(getattr(cls, method)))
            return cls
        return decorate(cls)

    def partial(self, name):
        event = self._add_event(name, breakpoint=True)

    def show(self):
        print(self.format())

    def format(self):
        return '\n'.join(
                         ['Crono' + '='*61 + ' exec_time = dry_time = n° exec_sum = dry_sum', ] +
                         [str(event) for event in self.events]
                )


from time import sleep
crono = Crono()


@crono.track
class A:
    def _a(self):
        sleep(0.4)
        self._b()
        self._c()

    def _b(self):
        sleep(0.3)
        self._d()

    def _c(self):
        crono.partial('TEST')
        sleep(0.2)
        crono.partial('TEST2')
        self._b()

    def _d(self):
        sleep(0.1)


a = A()


a._a()
a._d()
a._c()
crono.show()
