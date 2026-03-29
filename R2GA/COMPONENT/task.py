


class Task(object):

    def __init__(self, tid=0, name=None):
        self.id = tid
        self.name = name
        self.application = None
        self.is_entry = False
        self.is_exit = False
        self.is_pseudo = False
        self.processor__computation_time = {}
        self.successor__communication_time = {}
        self.successor__message = {}
        self.predecessor__communication_time = {}
        self.predecessor__message = {}
        self.successors = []
        self.predecessors = []
        self.all_successors = []
        self.all_predecessors = []
        self.in_degree = 0
        self.out_degree = 0
        self.average_computation_time = 0.0
        self.rank_up_value = 0.0
        self.rank_down_value = 0.0
        self.rank_sum_value = 0.0
        self.assignment = None
        self.out_messages = []
        self.in_messages = []
        self.is_decoded = False
        self.is_assigned = False

    def __str__(self):
        return "Task [name = %s]" % self.name