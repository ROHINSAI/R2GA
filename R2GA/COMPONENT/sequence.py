
from CONFIG.config import *

class Sequence(object):

    def __init__(self, chromosome=None, tsk_sequence=None, prossor_sequence=None, makespan=0.0, cost=0.0):
        self.chromosome = chromosome
        self.tsk_sequence = tsk_sequence
        self.prossor_sequence = prossor_sequence
        self.makespan = makespan
        self.cost = cost
        self.scheduling_list = None
