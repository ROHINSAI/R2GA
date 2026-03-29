


class RunningSpan(object):

    def __init__(self, start_time=0, finish_time=0):
        self.start_time = start_time
        self.finish_time = finish_time
        self.span = self.finish_time - self.start_time

    def __str__(self):

        return "[%.2f, %.2f]" % (self.start_time, self.finish_time)

