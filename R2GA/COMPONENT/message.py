
class Message(object):

    def __init__(self, mid=0, name=None):
        self.id = mid
        self.name = name
        self.source = None
        self.target = None
        self.transmission_time = 0.0
        self.rank_up_value = 0.0
        self.is_pseudo = False

    def rename(self, new_name):
        self.name = new_name

    def __str__(self):
        return "[" + self.name + "]"

