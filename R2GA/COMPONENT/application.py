

class Application(object):

    def __init__(self, name=None):
        self.tasknum = None
        self.processor_number = None
        self.name = name
        self.entry_task = []
        self.exit_task = []
        self.tasks = []
        self.prioritized_tasks = []
        self.deadline = 0.0
        self.task_groups_from_the_top = {}
        self.task_groups_from_the_bottom = {}
        self.all_messages = []
        self.valid_messages = []
        self.sequences = []

    def __str__(self):
        return "Application [name = %s]" % self.name

    def setDeadline(self, deadline):
        self.deadline = deadline