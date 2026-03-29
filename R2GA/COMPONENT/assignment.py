

class Assignment(object):

    def __init__(self, assigned_processor=None, running_span=None):
        self.assigned_processor = assigned_processor
        self.running_span = running_span

    def __str__(self):
        return "Assignment [assigned_processor = %s, running_span = %s]" % (self.assigned_processor, self.running_span)
