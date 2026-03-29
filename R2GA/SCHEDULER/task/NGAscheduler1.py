
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
import matplotlib.pyplot as plt
import numpy as np
from time import *


# ── Metric helpers ────────────────────────────────────────────────────────────

def _calc_system_utilization(scheduling_list, processor_number, makespan):
    if makespan <= 0 or processor_number <= 0:
        return 0.0
    busy = sum(
        (asgn.running_span.finish_time - asgn.running_span.start_time)
        for asgn in scheduling_list.list.values()
    )
    return busy / (makespan * processor_number)


def _calc_workload_balance(scheduling_list, processor_number):
    ft = {}
    for task, asgn in scheduling_list.list.items():
        pid = asgn.assigned_processor.id
        ft[pid] = max(ft.get(pid, 0.0), asgn.running_span.finish_time)
    if len(ft) < 2:
        return 0.0
    vals = [v for v in ft.values() if v > 0]
    return max(vals) - min(vals) if vals else 0.0


def _calc_energy(scheduling_list):
    speed_factors = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3}
    energy = 0.0
    for task, asgn in scheduling_list.list.items():
        pid = asgn.assigned_processor.id
        sf = speed_factors.get(pid, 1)
        duration = asgn.running_span.finish_time - asgn.running_span.start_time
        energy += duration * sf
    return energy


def _combined_fitness(makespan, workload_balance, energy, utilization):
    alpha = 0.1
    beta  = 0.01
    gamma = 0.5
    return makespan + alpha * workload_balance + beta * energy - gamma * utilization * makespan


# ── Scheduler class ───────────────────────────────────────────────────────────

class NGAScheduler1(Scheduler):

    sys.stdout = Logger('D:/pycpp/GABUDGET/result/result_task.html')

    def schedule(self, sign, app, outfilename, target, st):
        output_path = outfilename
        ComputingSystem.reset(app)
        pop_size = 500
        EliteRate = 0.2
        MutationRate = 0.02
        Elitepop = int(pop_size * EliteRate)
        population = self.init_population(app, pop_size)
        k = 0
        best_ans = []
        T = time()
        while k < 300:
            crossover_chromosomes = self.crossover(app, pop_size, population, Elitepop)
            for i in range(0, Elitepop):
                Elich = population[i].chromosome.copy()
                crossover_chromosomes.insert(0, Elich)

            mutation_chromosomes = self.mutate(app, pop_size, crossover_chromosomes, MutationRate)
            population = self.create_population(app, mutation_chromosomes)
            population.sort(key=lambda seq: seq.fitness)

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
        system_util = elite_sequence.system_util
        workload_balance = elite_sequence.workload_balance
        energy = elite_sequence.energy

        if outfilename == 'Appendix 1.txt':
            with open(output_path, 'a', encoding='utf-8') as file1:
                print(list(best_ans[i].makespan for i in range(k)), file=file1)
            print(list(best_ans[i].makespan for i in range(k)))

        output_path = outfilename
        with open(output_path, 'a', encoding='utf-8') as file1:
            print("The scheduler = %s, makespan = %.2f" % (self.scheduler_name, makespan), file=file1)
        print("The scheduler = %s, makespan = %.2f" % (self.scheduler_name, makespan))

        return makespan, cost, system_util, workload_balance, energy

    def init_population(self, app, pop_size):
        chromosomes = []
        uprank_tasks = app.tasks.copy()
        uprank_tasks.sort(key=lambda seq: seq.rank_up_value, reverse=True)
        chromosomes.append(uprank_tasks)

        downrank_tasks = app.tasks.copy()
        downrank_tasks.sort(key=lambda seq: seq.rank_down_value)
        chromosomes.append(downrank_tasks)

        candidate_tasks = []
        candidate_tasks += app.entry_task
        udrank_tasks = []
        for j in range(0, app.tasknum):
            candidate_tasks.sort(key=lambda tsk: tsk.rank_sum_value, reverse=True)
            task = candidate_tasks[0]
            udrank_tasks.append(task)
            task.is_decoded = True
            candidate_tasks.remove(task)
            for successor in task.successors:
                if self.is_ready(successor):
                    candidate_tasks.append(successor)
        chromosomes.append(udrank_tasks)

        for i in range(0, pop_size - 3):
            chromosome = []
            self.reset_tasks(app.tasks)
            candidate_tasks.clear()
            candidate_tasks += app.entry_task
            for j in range(0, app.tasknum):
                candidate_tasks.sort(key=lambda tsk: tsk.id)
                task = candidate_tasks[random.randint(0, len(candidate_tasks) - 1)]
                chromosome.append(task)
                task.is_decoded = True
                candidate_tasks.remove(task)
                for successor in task.successors:
                    if self.is_ready(successor):
                        candidate_tasks.append(successor)
            chromosomes.append(chromosome)

        population = self.create_population(app, chromosomes)
        population.sort(key=lambda seq: seq.fitness)
        return population

    def create_population(self, app, chromosomes):
        i = 0
        population = []
        processor_set = ComputingSystem.processors
        while chromosomes:

            ComputingSystem.reset(app)

            chromosome = chromosomes.pop(0)
            tsk_sequence = chromosome
            prossor_sequence = []
            processor = None

            scheduling_list = self.scheduling_lists.setdefault(i)

            if not scheduling_list:
                scheduling_list = SchedulingList("Scheduling_List_%d" % i)

            for task in tsk_sequence:
                earliest_start_time = 0.0
                earliest_finish_time = float("inf")
                for p in processor_set:
                    earliest_start_time_of_this_processor = SchedulerUtils.calculate_earliest_start_time(task, p)
                    earliest_finish_time_of_this_processor = earliest_start_time_of_this_processor + task.processor__computation_time[p]

                    if earliest_finish_time > earliest_finish_time_of_this_processor:
                        earliest_start_time = earliest_start_time_of_this_processor
                        earliest_finish_time = earliest_finish_time_of_this_processor
                        processor = p
                prossor_sequence.append(processor)
                running_span = RunningSpan(earliest_start_time, earliest_finish_time)
                assignment = Assignment(processor, running_span)

                task.assignment = assignment
                task.is_assigned = True

                processor.resident_tasks.append(task)
                processor.resident_tasks.sort(
                    key=lambda tsk: tsk.assignment.running_span.start_time)

                scheduling_list.list[task] = assignment
            makespan = calculate_makespan(scheduling_list)

            # ── new metrics ──────────────────────────────────────────────────
            system_util = _calc_system_utilization(scheduling_list, app.processor_number, makespan)
            workload_balance = _calc_workload_balance(scheduling_list, app.processor_number)
            energy = _calc_energy(scheduling_list)
            fitness = _combined_fitness(makespan, workload_balance, energy, system_util)
            # ─────────────────────────────────────────────────────────────────

            i = i + 1
            s = Sequence(chromosome, tsk_sequence, prossor_sequence, makespan)
            s.scheduling_list = scheduling_list
            s.system_util = system_util
            s.workload_balance = workload_balance
            s.energy = energy
            s.fitness = fitness
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

    def crossover(self, app, pop_size, population, Elitepop):
        flag = True
        offspring_population = []
        for i in range(Elitepop, pop_size):
            prev_chromosome1 = []
            next_chromosome1 = []
            prev_chromosome2 = []
            next_chromosome2 = []
            pop1 = random.randint(0, pop_size - 1)
            pop2 = random.randint(Elitepop + 1, pop_size - 1)
            while pop2 == pop1:
                pop1 = random.randint(0, pop_size - 1)
            crossover_point = random.randint(1, app.tasknum - 2)
            prev_chromosome1.extend(population[pop1].chromosome)
            next_chromosome1.extend(population[pop2].chromosome)
            prev_chromosome2.extend(population[pop1].chromosome)
            next_chromosome2.extend(population[pop2].chromosome)

            temp_l = prev_chromosome1.copy()
            delta = app.tasknum - 1
            for j in range(app.tasknum - 1, -1, -1):
                fd = False
                for k in range(crossover_point, -1, -1):
                    if next_chromosome1[j] == prev_chromosome1[k]:
                        fd = True
                        break
                if not fd:
                    prev_chromosome1[delta] = next_chromosome1[j]
                    delta -= 1
                    if delta <= crossover_point:
                        break
            delta = app.tasknum - 1
            for j in range(app.tasknum - 1, -1, -1):
                fd = False
                for k in range(crossover_point, -1, -1):
                    if temp_l[j] == next_chromosome1[k]:
                        fd = True
                        break
                if not fd:
                    next_chromosome1[delta] = temp_l[j]
                    delta -= 1
                    if delta <= crossover_point:
                        break

            temp_l = prev_chromosome2.copy()
            delta = 0
            for j in range(0, app.tasknum):
                fd = False
                for k in range(crossover_point, app.tasknum):
                    if next_chromosome2[j] == prev_chromosome2[k]:
                        fd = True
                        break
                if not fd:
                    prev_chromosome2[delta] = next_chromosome2[j]
                    delta += 1
                    if delta >= crossover_point:
                        break
            delta = 0
            for j in range(0, app.tasknum):
                fd = False
                for k in range(crossover_point, app.tasknum):
                    if temp_l[j] == next_chromosome2[k]:
                        fd = True
                        break
                if not fd:
                    next_chromosome2[delta] = temp_l[j]
                    delta += 1
                    if delta >= crossover_point:
                        break
            if flag:
                if random.randint(0, 1) % 2 == 0:
                    offspring_population.append(prev_chromosome1)
                else:
                    offspring_population.append(prev_chromosome2)
            else:
                if random.randint(0, 1) % 2 == 0:
                    offspring_population.append(next_chromosome1)
                else:
                    offspring_population.append(next_chromosome2)

            flag = not flag

        return offspring_population

    def mutate(self, app, pop_size, population, MutationRate):
        newpopulation = []
        for p in population:
            if random.random() < MutationRate:
                while True:
                    pos = random.randint(0, app.tasknum - 1)
                    taskid = p[pos]
                    FirstSUC = app.tasknum - 1
                    flag = True
                    if taskid.successors:
                        for i in range(pos + 1, app.tasknum):
                            for j in taskid.successors:
                                if j == p[i]:
                                    FirstSUC = i
                                    flag = False
                                    break
                            if not flag:
                                break
                    if FirstSUC - pos < 2:
                        continue

                    k = random.randint(pos + 1, FirstSUC)
                    taskk = p[k]
                    fll = True
                    if taskk.predecessors:
                        for i in range(pos, k):
                            for j in taskk.predecessors:
                                if j == p[i]:
                                    fll = False
                                    break
                            if not fll:
                                break
                    if fll:
                        break
                    else:
                        continue
                p[pos], p[k] = p[k], p[pos]
                newpopulation.append(p)
            else:
                newpopulation.append(p)
        return newpopulation
