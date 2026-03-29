

class TaskGroup(object):

    def __init__(self, group_id=0):
        self.group_id = group_id
        self.tasks = []

    def __str__(self):
        return "Group [group_id = %d, tasks = %s]" % (self.group_id, self.tasks)
