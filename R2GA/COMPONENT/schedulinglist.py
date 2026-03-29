
class SchedulingList(object):

    def __init__(self, list_name=None):
        self.list = {}
        self.makespan = 0.0

    def __str__(self):
        return "SchedulingList [list = %s]" % self.list

