
from CONFIG.config import *
from COMPONENT.application import Application
from COMPONENT.task import Task
from COMPONENT.taskgroup import TaskGroup
from COMPONENT.message import Message
from COMPONENT.messagegroup import MessageGroup
from system.computingsystem import ComputingSystem
from UTIL.genericutils import print_list
from UTIL.schedulerutils import SchedulerUtils
from UTIL.genericutils import *


class ApplicationService(object):

    @staticmethod
    def init_application(Scheduler, app, task_number, computation_time_matrix, computation_cost_matrix, communication_time_matrix):

        ApplicationService.__init_task_list(app, task_number)
        ApplicationService.__init_computation_time(app, computation_time_matrix)

        ApplicationService.__init_successor(app, communication_time_matrix)
        ApplicationService.__init_predecessor(app)

        ApplicationService.__init_all_successor(app)
        ApplicationService.__init_all_predecessor(app)

        if Scheduler.scheduler_name == 'NGA' or Scheduler.scheduler_name == 'HGA':
            ApplicationService.__calculate_rank_up_value(app)
            ApplicationService.__calculate_rank_down_value(app)
            ApplicationService.__calculate_rank_sum_value(app)

        ApplicationService.__tag_entry_and_exit_task(app)

        if Scheduler.scheduler_name == 'LWSGA':
            ApplicationService.__group_task_from_the_top(app)

        pass

    @staticmethod
    def __init_task_list(app, task_number):
        app.tasknum = task_number
        for i in range(task_number):
            t = Task((i + 1), "%s-task-%d" % (app.name, (i + 1)))
            t.application = app
            app.tasks.append(t)
            app.prioritized_tasks.append(t)

    @staticmethod
    def __init_computation_time(app, computation_time_matrix):

        if not computation_time_matrix:
            return

        processors = ComputingSystem.processors

        for i in range(len(app.tasks)):
            task = app.tasks[i]
            s = 0.0
            for j in range(len(processors)):
                processor = processors[j]
                computation_time = computation_time_matrix[i][j]
                task.processor__computation_time[processor] = computation_time
                s = s + computation_time
            lenprocessors = len(processors)
            app.processor_number = lenprocessors
            task.average_computation_time = s / lenprocessors

    @staticmethod
    def __init_computation_cost(app, computation_cost_matrix):

        if not computation_cost_matrix:
            return

        processors = ComputingSystem.processors

        for i in range(len(app.tasks)):
            task = app.tasks[i]
            s = 0.0
            for j in range(len(processors)):
                processor = processors[j]
                computation_cost = computation_cost_matrix[i][j]
                task.processor__computation_cost[processor] = computation_cost
                s = s + computation_cost
            task.average_computation_cost = s / len(processors)

    @staticmethod
    def __init_successor(app, communication_time_matrix):

        if not communication_time_matrix:
            return

        k = 0

        for i in range(len(app.tasks)):
            task = app.tasks[i]
            communication_times = communication_time_matrix[i]
            for j in range(len(communication_times)):
                communication_time = communication_times[j]
                if communication_time != INF:
                    successor = app.tasks[j]
                    task.successor__communication_time[successor] = communication_time
                    task.successors.append(successor)

                    k = k + 1

                    message = Message(k, "m%d,%d" % (i + 1, j + 1))
                    message.source = task
                    message.target = successor
                    message.transmission_time = communication_time
                    app.all_messages.append(message)
                    if message.transmission_time > 0.0:
                        app.valid_messages.append(message)
                    else:
                        message.is_pseudo = True

                    task.successor__message[successor] = message

                    task.out_messages.append(message)
                    successor.in_messages.append(message)

            task.out_degree = len(task.successors)

    @staticmethod
    def __init_predecessor(app):
        for i in range(len(app.tasks)):
            task = app.tasks[i]
            for successor in task.successors:
                communication_time = task.successor__communication_time[successor]
                successor.predecessor__communication_time[task] = communication_time
                successor.predecessors.append(task)

                message = task.successor__message[successor]
                successor.predecessor__message[task] = message

            task.in_degree = len(task.predecessors)

    @staticmethod
    def __init_all_successor(app):
        for i in range(len(app.tasks) - 1, -1, -1):
            task = app.tasks[i]
            if task.is_exit:
                task.all_successors.extend([])
            else:
                successors = task.successors
                task.all_successors.extend(successors)
                for successor in successors:
                    task.all_successors.extend(successor.all_successors)
                compact_list = list(set(task.all_successors))
                compact_list.sort(key=lambda t: t.id)
                task.all_successors.clear()
                task.all_successors.extend(compact_list)

    @staticmethod
    def __init_all_predecessor(app):
        for i in range(len(app.tasks)):
            task = app.tasks[i]
            if task.is_entry:
                task.all_predecessors.extend([])
            else:
                predecessors = task.predecessors
                task.all_predecessors.extend(predecessors)
                for predecessor in predecessors:
                    task.all_predecessors.extend(predecessor.all_predecessors)
                compact_list = list(set(task.all_predecessors))
                compact_list.sort(key=lambda t: t.id)
                task.all_predecessors.clear()
                task.all_predecessors.extend(compact_list)

    @staticmethod
    def __init_message(app):
        for message in app.all_messages:
            source = message.source
            target = message.target
            all_predecessors_of_source = source.all_predecessors
            all_successors_of_target = target.all_successors

            all_in_messages = []
            all_out_messages = []

            all_in_messages.extend(source.in_messages)
            all_out_messages.extend(target.out_messages)

            for predecessor in all_predecessors_of_source:
                all_in_messages.extend(predecessor.in_messages)
            for successor in all_successors_of_target:
                all_out_messages.extend(successor.out_messages)

            compact_in_messages = list(set(all_in_messages))
            compact_out_messages = list(set(all_out_messages))

            message.all_predecessor_messages.extend(compact_in_messages)
            message.all_successor_messages.extend(compact_out_messages)

            for predecessor_message in message.all_predecessor_messages:
                message.all_predecessor_messages_lite.append(predecessor_message.name)
            for successor_message in message.all_successor_messages:
                message.all_successor_messages_lite.append(successor_message.name)

    @staticmethod
    def __calculate_rank_up_value(app):
        for i in range(len(app.tasks) - 1, -1, -1):
            task = app.tasks[i]
            temp_value = 0.0
            if task.successors:
                for successor in task.successors:
                    successor_rank_up_value = successor.rank_up_value
                    successor_communication_time = task.successor__communication_time[successor]
                    if (successor_rank_up_value + successor_communication_time) > temp_value:
                        temp_value = successor_rank_up_value + successor_communication_time

            task.rank_up_value = task.average_computation_time + temp_value

            for message in task.in_messages:
                message.rank_up_value = task.rank_up_value + message.transmission_time

    @staticmethod
    def __calculate_rank_down_value(app):
        for task in app.tasks:
            temp_value = 0.0
            if task.predecessors:
                for predecessor in task.predecessors:
                    average_computation_time_of_predecessor = predecessor.average_computation_time
                    rank_down_value_of_predecessor = predecessor.rank_down_value
                    communication_time_of_predecessor = task.predecessor__communication_time[predecessor]
                    if (rank_down_value_of_predecessor + average_computation_time_of_predecessor + communication_time_of_predecessor) > temp_value:
                        temp_value = rank_down_value_of_predecessor + average_computation_time_of_predecessor + communication_time_of_predecessor

            task.rank_down_value = temp_value

    @staticmethod
    def __calculate_rank_sum_value(app):
        for task in app.tasks:
            task.rank_sum_value = task.rank_up_value + task.rank_down_value

    @staticmethod
    def __calculate_tradeoff_with_alpha_and_beta(app, alpha, beta):

        processors = ComputingSystem.processors

        for i in range(len(app.tasks)):
            task = app.tasks[i]
            for j in range(len(processors)):
                processor = processors[j]
                time = task.processor__computation_time[processor]
                cost = task.processor__computation_cost[processor]
                task.processor__tradeoff[processor] = time * alpha + cost * beta

    @staticmethod
    def __tag_entry_and_exit_task(app):
        for task in app.tasks:
            if not task.predecessors:
                task.is_entry = True
                app.entry_task.append(task)
            if not task.successors:
                task.is_exit = True
                app.exit_task.append(task)

    @staticmethod
    def __tag_critical_task(app):
        rsv = 0
        for i in app.entry_task:
            if i.rank_sum_value > rsv:
                task = i
                rsv = i.rank_sum_value

        task.is_critical = True
        app.critical_tasks.append(task)

        while True:
            temp_task = None
            temp_rank_sum_value = 0.0
            for successor in task.successors:
                if successor.rank_sum_value > temp_rank_sum_value:
                    temp_task = successor
                    temp_rank_sum_value = successor.rank_sum_value

            task = temp_task
            task.is_critical = True
            app.critical_tasks.append(task)

            if task.is_exit:
                break
            if not task.successors:
                break

    @staticmethod
    def __sort_tasks(app):
        app.prioritized_tasks.sort(key=lambda task: task.rank_up_value, reverse=True)

    @staticmethod
    def __calculate_cp_min_x(app):
        cp_min_time_sum = 0.0
        cp_min_cost_sum = 0.0
        for task in app.critical_tasks:
            min_time = INF
            min_cost = INF
            for processor in ComputingSystem.processors:
                time = task.processor__computation_time[processor]

                if min_time > time:
                    min_time = time

            cp_min_time_sum = cp_min_time_sum + min_time

        app.cp_min_time = cp_min_time_sum

    @staticmethod
    def __group_task_from_the_top(app):
        app.task_groups_from_the_top.clear()
        groups = app.task_groups_from_the_top
        tasks = app.tasks
        for task in tasks:
            k = SchedulerUtils.get_the_max_steps_to_the_entry(task.predecessors)
            group = groups.setdefault(k)
            if not group:
                group = TaskGroup(k)
                groups[k] = group

            group.tasks.append(task)

        sorted_task_groups_from_the_top = sorted(groups.items(), key=lambda item: item[0])
        app.task_groups_from_the_top.clear()
        for task_group_id, taskgroup in sorted_task_groups_from_the_top:
            app.task_groups_from_the_top[task_group_id] = taskgroup

    @staticmethod
    def __group_message_from_the_top(app):
        taskgroups = app.task_groups_from_the_top
        messagegroups = app.message_groups_from_the_top
        for task_group_id, taskgroup in taskgroups.items():
            messagegroup = messagegroups.setdefault(task_group_id)
            if not messagegroup:
                messagegroup = MessageGroup(task_group_id)
                messagegroups[task_group_id] = messagegroup

            tsk_list = taskgroup.tasks
            for task in tsk_list:
                for message in task.out_messages:
                    messagegroup.messages.append(message)

    @staticmethod
    def __group_task_from_the_bottom(app):
        groups = app.task_groups_from_the_bottom
        tasks = app.tasks
        for task in tasks:
            k = SchedulerUtils.get_the_max_steps_to_the_exit(task.successors)
            group = groups.setdefault(k)
            if not group:
                group = TaskGroup(k)
                groups[k] = group

            group.tasks.append(task)
