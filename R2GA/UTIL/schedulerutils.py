
from datetime import datetime
from copy import *
import random


class SchedulerUtils(object):

    @classmethod
    def calculate_earliest_start_time(cls, task, processor):

        predecessor_available_time = 0.0
        processor_available_time = 0.0

        resident_tasks = processor.resident_tasks

        if resident_tasks:
            for t in resident_tasks:
                if t.application == task.application:
                    temp_finish_time = t.assignment.running_span.finish_time
                    if processor_available_time < temp_finish_time:
                        processor_available_time = temp_finish_time

        if task.is_entry:
            earliest_start_time = processor_available_time
        else:
            for predecessor in task.predecessors:
                assigned_processor_of_predecessor = predecessor.assignment.assigned_processor
                if processor == assigned_processor_of_predecessor:
                    communication_time = 0.0
                else:
                    communication_time = task.predecessor__communication_time[predecessor]

                finish_time_of_predecessor = predecessor.assignment.running_span.finish_time

                if (finish_time_of_predecessor + communication_time) > predecessor_available_time:
                    predecessor_available_time = finish_time_of_predecessor + communication_time

            earliest_start_time = processor_available_time if processor_available_time > predecessor_available_time else predecessor_available_time

        return earliest_start_time

    @classmethod
    def IPPS_calculate_earliest_start_time(cls, task, processor, chromosome_dex):

        predecessor_available_time = 0.0
        processor_available_time = 0.0

        resident_tasks = processor.resident_tasks

        if resident_tasks:
            for t in resident_tasks:
                if t.application == task.application:
                    temp_finish_time = t.assignment.running_span.finish_time
                    if processor_available_time < temp_finish_time:
                        processor_available_time = temp_finish_time

        if task.is_entry:
            earliest_start_time = processor_available_time
        else:
            for predecessor in task.predecessors:
                if predecessor.id not in chromosome_dex:
                    continue
                assigned_processor_of_predecessor = predecessor.assignment.assigned_processor
                if processor == assigned_processor_of_predecessor:
                    communication_time = 0.0
                else:
                    communication_time = task.predecessor__communication_time[predecessor]

                finish_time_of_predecessor = predecessor.assignment.running_span.finish_time

                if (
                    finish_time_of_predecessor + communication_time) > predecessor_available_time:
                    predecessor_available_time = finish_time_of_predecessor + communication_time

            earliest_start_time = processor_available_time if processor_available_time > predecessor_available_time else predecessor_available_time

        return earliest_start_time

    @classmethod
    def calculate_earliest_finish_time(cls, task, processor):
        earliest_start_time = cls.calculate_earliest_start_time(task, processor)
        computation_time = task.processor__computation_time[processor]
        earliest_finish_time = earliest_start_time + computation_time
        return earliest_finish_time

    @classmethod
    def get_the_mini_computation_time_processor(cls, tasks, processors):
        processor = None

        min_computation_time = float("inf")

        for p in processors:
            computation_time = 0.0
            for task in tasks:
                computation_time += task.processor__computation_time[p]

            if min_computation_time > computation_time:
                min_computation_time = computation_time
                processor = p

        return processor

    @classmethod
    def is_ready(cls, task):
        flag = True
        if task.predecessors:
            for predecessor in task.predecessors:
                flag = flag and predecessor.is_assigned

        return flag

    @classmethod
    def get_the_max_steps_to_the_entry(cls, predecessors):
        max_steps = 0

        if not predecessors:
            max_steps = 0
        else:
            for predecessor in predecessors:
                steps = cls.get_the_max_steps_to_the_entry(predecessor.predecessors) + 1
                if steps > max_steps:
                    max_steps = steps

        return max_steps

    @classmethod
    def get_the_max_steps_to_the_exit(cls, successors):
        max_steps = 0

        if not successors:
            max_steps = 0
        else:
            for successor in successors:
                steps = cls.get_the_max_steps_to_the_exit(successor.successors) + 1
                if steps > max_steps:
                    max_steps = steps

        return max_steps

    @classmethod
    def find_message_by_name(cls, messages, name):
        for msg in messages:
            if msg.name == name:
                return msg

    @classmethod
    def has_predecessor(cls, message, rear):
        flag = False
        predecessors = message.all_predecessor_messages_lite
        for msg in rear:
            if msg in predecessors:
                flag = True
        return flag

    @classmethod
    def has_successor(cls, message, head):
        flag = False
        successors = message.all_successor_messages_lite
        for msg in head:
            if msg in successors:
                flag = True
        return flag

    @classmethod
    def swap(cls, msg_list, i, j):
        msg = msg_list[i]
        msg_list[i] = msg_list[j]
        msg_list[j] = msg

    @classmethod
    def generate_valid_sequences(cls, app, messages, messages_lite, begin, end):
        if begin == end:
            include = True
            for i in range(len(messages_lite)):
                i_msg = SchedulerUtils.find_message_by_name(messages, messages_lite[i])
                for j in range((i + 1), len(messages_lite)):
                    j_msg = SchedulerUtils.find_message_by_name(messages, messages_lite[j])
                    if j_msg in i_msg.all_predecessor_messages or i_msg in j_msg.all_successor_messages:
                        include = False
                        break
                if not include:
                    break
            if include:
                msg_sequence = deepcopy(messages_lite)
                app.sequences.append(msg_sequence)
                print("%d ---- %s ---- %s" % (len(app.sequences), (datetime.now().strftime('%Y-%m-%d %H:%M:%S %f')), msg_sequence))
            pass

        for i in range(begin, (end + 1)):
            cls.swap(messages_lite, begin, i)
            cls.generate_valid_sequences(app, messages, messages_lite, begin + 1, end)
            cls.swap(messages_lite, begin, i)
        pass

    @classmethod
    def init_population(cls, app, messages, messages_lite, begin, end, size):
        if begin == end:
            include = True
            for i in range(len(messages_lite)):
                i_msg = SchedulerUtils.find_message_by_name(messages, messages_lite[i])
                for j in range((i + 1), len(messages_lite)):
                    j_msg = SchedulerUtils.find_message_by_name(messages, messages_lite[j])
                    if j_msg in i_msg.all_predecessor_messages or i_msg in j_msg.all_successor_messages:
                        include = False
                        break
                if not include:
                    break
            if include:
                msg_sequence = deepcopy(messages_lite)
                app.sequences.append(msg_sequence)
                count = len(app.sequences)
                if count > size:
                    return

            pass

        for i in range(begin, (end + 1)):
            cls.swap(messages_lite, begin, i)
            cls.init_population(app, messages, messages_lite, begin + 1, end, size)
            cls.swap(messages_lite, begin, i)
        pass

    @classmethod
    def generateComputationMatrix(cls, taskNumber, processorNumber):
        computationMatrix = []
        upper = 20
        lower = 5
        for i in range(taskNumber):
            temp = []
            for j in range(processorNumber):
                v = lower + random.randint(0, upper)
                cost = float(v)
                temp.append(cost)
            computationMatrix.append(temp)
        return computationMatrix

    @classmethod
    def generateCommunicationMatrixGaussian(cls, m):
        taskNumber = int((m * m + m - 2) / 2)
        communicationMatrix = []
        upper = 27
        lower = 10

        end = m - 1
        k = 2
        level = m - 1
        for i in range(taskNumber):
            temp = []
            for j in range(taskNumber):
                temp.append(0.0)
            if i == 0 and (j > 0 and j < m):
                temp[j] = float(lower + random.randint(0, upper))
            communicationMatrix.append(temp)
        for i in range(taskNumber):
            for j in range(i, taskNumber):
                if i == end + 1:
                    for a in range(i + 1, i + 1 + m - k):
                        communicationMatrix[i][a] = float(lower + random.randint(0, upper))
                    end = end + 1 + (m - k)
                    k = k + 1
                    level = level - 1
                    break
                if i > 0 and j == (i + level):
                    communicationMatrix[i][j] = float(lower + random.randint(0, upper))
        return communicationMatrix