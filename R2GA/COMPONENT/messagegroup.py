

class MessageGroup(object):

    def __init__(self, group_id=0):
        self.group_id = group_id
        self.messages = []

    def __str__(self):
        return "Group [group_id = %d, messages = %s]" % (self.group_id, self.messages)
