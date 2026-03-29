
class Processor(object):

    def __init__(self, pid=0, name=None):
        self.id = pid
        self.name = name
        self.resident_tasks = []

    def __str__(self):
        return "Processor [id = %d, name = %s]" % (self.id, self.name)