from datetime import datetime
from inspect import getmembers, ismethod


class CronoEvent:
    def __init__(self, agent):
        self.agent = agent
        self.start_t = self.stop_t = self.parent = None
        self.childs = []
        self.parent = None
        self.depth = 1

    def start(self):
        self.start_t = datetime.now()

    def stop(self):
        self.stop_t = datetime.now()

    def _set_child(self, child):
        self.childs.append(child)
        child.depth = self.depth + 1
        child.parent = self

    def __repr__(self):
        return f'{self.agent.__name__.ljust(50-(self.depth*8), " ")} - {self.stop_t - self.start_t} | {self._childs_repr()}'

    def _childs_repr(self):
        depth = '\t' * self.depth
        return ''.join(f'\n{depth}{c}' for c in self.childs)


class Crono:

    def __init__(self):
        self.events = []
        self.curr_event = None

    def _add_event(self, method):
        event = CronoEvent(method)
        if self.curr_event:
            self.curr_event._set_child(event)
        else:
            self.events.append(event)
        self.curr_event = event
        event.start()
        return event

    def _stop_event(self, event):
        event.stop()
        if event.parent:
            self.curr_event = event.parent

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

    def show(self):
        print('Crono ------------')
        for event in self.events:
            print(event)


from time import sleep
crono = Crono()


@crono.track
class A:
    def _a(self):
        print('_a')
        sleep(0.5)
        self._b()
        self._c()

    def _b(self):
        print('_b')
        sleep(1)
        self._d()

    def _c(self):
        print('_c')
        sleep(0.7)
        self._b()

    def _d(self):
        sleep(0.1)


a = A()


a._a()
a._d()
a._c()
crono.show()
