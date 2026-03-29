
from COMPONENT.schedulinglist import SchedulingList

class Scheduler(object):

    def __init__(self, scheduler_name):
        self.scheduler_name = scheduler_name
        self.task_scheduling_list = SchedulingList("TaskSchedulingList")
        self.canfd_scheduling_list = SchedulingList("CanSchedulingList")
        self.scheduling_lists = {}

    def reset(self):
        self.task_scheduling_list.list.clear()
        self.canfd_scheduling_list.list.clear()

        self.task_scheduling_list.messages.clear()
        self.canfd_scheduling_list.messages.clear()

        self.task_scheduling_list.makespan = 0.0
        self.canfd_scheduling_list.makespan = 0.0

        self.task_scheduling_lists.clear()
        self.canfd_scheduling_lists.clear()
