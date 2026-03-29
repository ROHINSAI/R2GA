
import sys
import os
from SCHEDULER.scheduler import Scheduler
from system.computingsystem import ComputingSystem
from UTIL.schedulerutils import SchedulerUtils
from COMPONENT.runningspan import RunningSpan
from COMPONENT.assignment import Assignment
from COMPONENT.sequence import Sequence
from COMPONENT.schedulinglist import SchedulingList
from UTIL.genericutils import *
from UTIL.logger import Logger
from CONFIG.config import *
from itertools import permutations, product
from datetime import datetime
from copy import *
import random
from time import *
import matplotlib.pyplot as plt
import numpy as np


class GeneticScheduler(Scheduler):

    sys.stdout = Logger('D:/pycpp/GABUDGET/result/result_task.html')

    def schedule(self, sign, app, outfilename, target, st):
        output_path = outfilename
        ComputingSystem.reset(app)
        pop_size = 500
        population = self.init_population(app, pop_size)
        k = 0
        best_ans = []
        T = time()
        s = pop_size // 2
        while k < 300:
            half_population = []
            half_population.extend(self.select(pop_size, population, s))
            crossover_chromosomes = self.crossover(app, pop_size, population, s)
            mutation_chromosomes = self.mutate(app, crossover_chromosomes)
            population = population[:s]
            population.extend(self.create_population(app, mutation_chromosomes))
            population.sort(key=lambda seq: seq.makespan)

            best_ans.append(population[0])
            if outfilename == 'Appendix 1.txt':
                k = k + 1
            if outfilename == 'Appendix 3.txt':
                if population[0].makespan <= target:
                    break
            if outfilename == 'Appendix 4.txt':
                T = time()
            if T - st >= target:
                break

        elite_sequence = population[0]
        makespan = elite_sequence.makespan
        cost = elite_sequence.cost

        if outfilename == 'Appendix 1.txt':
            with open(output_path, 'a', encoding='utf-8') as file1:
                print(list(best_ans[i].makespan for i in range(k)), file=file1)
            print(list(best_ans[i].makespan for i in range(k)))

        output_path = outfilename
        with open(output_path, 'a', encoding='utf-8') as file1:
            print("The scheduler = %s, makespan = %.2f" % (self.scheduler_name, makespan), file=file1)
        print("The scheduler = %s, makespan = %.2f" % (self.scheduler_name, makespan))

        return makespan, cost

    def init_population(self, app, pop_size):
        chromosomes = []

        uprank_tasks = app.tasks.copy()
        uprank_tasks.sort(key=lambda seq: seq.rank_up_value, reverse=True)

        uprank_tasks_pro = self.Allocation_processor(app, uprank_tasks)

        candidate_tasks = []
        chromosome1 = []
        chromosome2 = []
        candidate_tasks += app.entry_task
        self.reset_tasks(app.tasks)
        for j in range(0, app.tasknum):
            candidate_tasks.sort(key=lambda tsk: tsk.id)
            task = uprank_tasks[j]
            tadex = candidate_tasks.index(task)
            l = len(candidate_tasks)
            gene = tadex / l + random.random() / l
            chromosome1.append(gene)
            task.is_decoded = True
            candidate_tasks.remove(task)
            for successor in task.successors:
                if self.is_ready(successor):
                    candidate_tasks.append(successor)
            chromosome2.append((uprank_tasks_pro[j] - 1) / app.processor_number + random.random() / app.processor_number)
        chromosomes.append(chromosome1 + chromosome2)

        for i in range(1, pop_size):
            chromosome = []
            for j in range(0, 2 * app.tasknum):
                chromosome.append(random.random())
            chromosomes.append(chromosome)

        population = self.create_population(app, chromosomes)
        population.sort(key=lambda seq: seq.makespan)
        return population

    def create_population(self, app, chromosomes):
        i = 0
        population = []
        candidate_tasks = []
        processor_set = ComputingSystem.processors
        while chromosomes:
            self.reset_tasks(app.tasks)
            candidate_tasks.clear()
            candidate_tasks += app.entry_task
            chromosome = chromosomes.pop(0)

            tsk_sequence = []
            prossor_sequence = []
            for j in range(0, app.tasknum):
                gene = chromosome[j]
                candidate_tasks.sort(key=lambda tsk: tsk.id)
                size = len(candidate_tasks)

                tsk_index = int(gene * size)

                task = candidate_tasks[tsk_index]
                task.is_decoded = True
                tsk_sequence.append(task)
                candidate_tasks.remove(task)
                for successor in task.successors:
                    if self.is_ready(successor):
                        candidate_tasks.append(successor)

                prossor_gene = chromosome[app.tasknum + j]
                processor_set.sort(key=lambda prossor: prossor.id)

                prossor_index = int(prossor_gene * app.processor_number)
                processor = processor_set[prossor_index]
                prossor_sequence.append(processor)

            makespan, scheduling_list = self.calculate_response_time_and_cost(app, i, tsk_sequence, prossor_sequence)

            i = i + 1
            s = Sequence(chromosome, tsk_sequence, prossor_sequence, makespan)
            s.scheduling_list = scheduling_list
            population.append(s)

        return population

    def reset_tasks(self, tasks):
        for task in tasks:
            task.is_decoded = False

    def is_ready(self, task):
        for predecessor in task.predecessors:
            if not predecessor.is_decoded:
                return False
        return True

    def calculate_response_time_and_cost(self, app, counter, task_sequence, processor_sequence):
        ComputingSystem.reset(app)

        scheduling_list = self.scheduling_lists.setdefault(counter)

        if not scheduling_list:
            scheduling_list = SchedulingList("Scheduling_List_%d" % counter)

        for i in range(0, app.tasknum):
            task = task_sequence[i]
            processor = processor_sequence[i]

            start_time = SchedulerUtils.calculate_earliest_start_time(task, processor)
            finish_time = start_time + task.processor__computation_time[processor]

            running_span = RunningSpan(start_time, finish_time)
            assignment = Assignment(processor, running_span)

            task.assignment = assignment

            task.is_assigned = True

            processor.resident_tasks.append(task)
            processor.resident_tasks.sort(key=lambda tsk: tsk.assignment.running_span.start_time)

            scheduling_list.list[task] = assignment

        makespan = calculate_makespan(scheduling_list)

        scheduling_list.makespan = makespan

        return makespan, scheduling_list

    def select(self, pop_size, population, s):
        half_population = population[:s]
        return half_population

    def crossover(self, app, pop_size, population, s):
        offspring_population = []
        for i in range(0, s - 1, 2):
            prev_chromosome = []
            next_chromosome = []
            prev_chromosome.extend(population[i].chromosome)
            next_chromosome.extend(population[i + 1].chromosome)
            crossover_point1 = random.randint(1, app.tasknum - 2)
            crossover_point2 = random.randint(app.tasknum + 1, 2 * app.tasknum - 2)
            for j in range(crossover_point1, crossover_point2):
                prev_chromosome[j], next_chromosome[j] = next_chromosome[j], prev_chromosome[j]
            offspring_population.append(prev_chromosome)
            offspring_population.append(next_chromosome)

        return offspring_population

    def mutate(self, app, population):
        for p in population:
            pos1 = random.randint(0, app.tasknum - 1)
            pos2 = random.randint(app.tasknum, 2 * app.tasknum - 1)
            p[pos1] = random.random()
            p[pos2] = random.random()
        return population
        pass

    def Allocation_processor(self, app, tasks):
        ComputingSystem.reset(app)

        processors = ComputingSystem.processors

        processor = None
        temp_task_id = []
        temp_processor_id = []

        for task in tasks:

            earliest_start_time = 0.0
            earliest_finish_time = float("inf")

            for p in processors:

                earliest_start_time_of_this_processor = SchedulerUtils.calculate_earliest_start_time(task, p)
                earliest_finish_time_of_this_processor = earliest_start_time_of_this_processor + task.processor__computation_time[p]

                if earliest_finish_time > earliest_finish_time_of_this_processor:
                    earliest_start_time = earliest_start_time_of_this_processor
                    earliest_finish_time = earliest_finish_time_of_this_processor
                    processor = p

            running_span = RunningSpan(earliest_start_time, earliest_finish_time)
            assignment = Assignment(processor, running_span)
            task.assignment = assignment

            task.is_assigned = True

            processor.resident_tasks.append(task)
            temp_task_id.append(task.id)

            temp_processor_id.append(processor.id)
            processor.resident_tasks.sort(
                key=lambda tsk: tsk.assignment.running_span.start_time)
        return temp_processor_id
