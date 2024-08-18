import time

class Profiler:
    last_mark: None
    start_mark: None

    def start(self):
        self.last_mark = self.time_mark()
        self.start_mark = self.last_mark

    def time_mark(self):
        return time.perf_counter(), time.process_time()

    def profile(self, funcName, t1 = None):
        if (t1 is None and self.last_mark is None):
            print("Profiler is not started properly")
            return
        elif (t1 is None):
            t1 = self.last_mark
        t2 = self.time_mark()
        self.last_mark = t2
        print(funcName)
        print(f" Real time: {t2[0] - t1[0]:.8f} s")
        if self.start_mark is not None:
            print(f" Total time from start: {t2[0] - self.start_mark[0]:.8f} s")
        print()
        