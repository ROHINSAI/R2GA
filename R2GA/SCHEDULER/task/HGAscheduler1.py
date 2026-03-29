
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

class HGAScheduler1(Scheduler):

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
            half_population = []
            half_population.extend(self.select(pop_size, population, Elitepop))
            crossover_offspring = self.crossover(pop_size, app, half_population)
            mutation_offspring = self.mutate(app, crossover_offspring, MutationRate)
            population = population[:Elitepop]
            population.extend(mutation_offspring)
            population = self.RscLoadAdjust(pop_size, app, population)
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
        tasks = app.tasks
        app.tasks.sort(key=lambda seq: seq.rank_up_value, reverse=True)
        for i in range(0, pop_size):
            chromosome = []
            for j in range(0, app.tasknum):
                chromosome.append(random.randint(0, app.processor_number - 1))
            chromosomes.append(chromosome)

        population = self.create_population(app, chromosomes)
        population.sort(key=lambda seq: seq.fitness)
        return population

    def create_population(self, app, chromosomes):
        i = 0
        population = []

        processor_set = ComputingSystem.processors
        while chromosomes:
            chromosome = chromosomes.pop(0)

            tsk_sequence = app.tasks

            prossor_sequence = []
            for j in range(0, app.tasknum):
                prossor_gene = chromosome[j]
                processor_set.sort(key=lambda prossor: prossor.id)
                processor = processor_set[prossor_gene]
                prossor_sequence.append(processor)
            makespan, scheduling_list = self.calculate_response_time_and_cost(app, i, tsk_sequence, prossor_sequence)

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

    def select(self, pop_size, population, Elitepop):
        half_population = []
        for i in range(Elitepop, pop_size - 1, 2):
            p1 = random.randint(0, pop_size - 1)
            p2 = random.randint(0, pop_size - 1)
            while p1 == p2:
                p2 = random.randint(0, pop_size - 1)
            if p1 < p2:
                parent1 = p1
            else:
                parent1 = p2
            parent2 = parent1
            while parent2 == parent1:
                p1 = random.randint(0, pop_size - 1)
                p2 = random.randint(0, pop_size - 1)
                while p1 == p2:
                    p2 = random.randint(0, pop_size - 1)
                if p1 < p2:
                    parent2 = p1
                else:
                    parent2 = p2
            half_population.append(population[parent1])
            half_population.append(population[parent2])
        return half_population

    def crossover(self, pop_size, app, population):
        offspring_population = []
        for i in range(0, len(population) - 1, 2):
            temp_l = []
            prev_chromosome1 = []
            next_chromosome1 = []
            prev_chromosome1.extend(population[i].chromosome)
            next_chromosome1.extend(population[i + 1].chromosome)
            crossover_point = random.randint(1, app.tasknum - 1)
            for j in range(crossover_point):
                prev_chromosome1[j], next_chromosome1[j] = next_chromosome1[j], prev_chromosome1[j]
            temp_l.append(prev_chromosome1)
            temp_l.append(next_chromosome1)

            prev_chromosome2 = []
            next_chromosome2 = []
            prev_chromosome2.extend(population[i].chromosome)
            next_chromosome2.extend(population[i + 1].chromosome)
            crossover_point1 = random.randint(1, app.tasknum - 1)
            crossover_point2 = random.randint(1, app.tasknum - 1)
            while crossover_point1 == crossover_point2:
                crossover_point2 = random.randint(1, app.tasknum - 1)
            if crossover_point1 > crossover_point2:
                crossover_point1, crossover_point2 = crossover_point2, crossover_point1
            for j in range(crossover_point1, crossover_point2):
                prev_chromosome2[j], next_chromosome2[j] = next_chromosome2[j], prev_chromosome2[j]
            temp_l.append(prev_chromosome2)
            temp_l.append(next_chromosome2)
            temp_l = self.create_population(app, temp_l)
            temp_l.sort(key=lambda seq: seq.fitness)
            offspring_population.append(temp_l[0])
            offspring_population.append(temp_l[1])

        return offspring_population

    def mutate(self, app, population, MutationRate):
        newpopulation = []
        for p in population:
            if random.random() < MutationRate:
                temp = []
                temp1 = p.chromosome
                temp2 = p.chromosome
                pos = random.randint(0, app.tasknum - 1)
                temp1[pos] = random.randint(0, app.processor_number - 1)

                pos1 = random.randint(0, app.tasknum - 1)
                pos2 = random.randint(0, app.tasknum - 1)
                while pos1 == pos2:
                    pos2 = random.randint(0, app.tasknum - 1)
                temp2[pos1] = random.randint(0, app.processor_number - 1)
                temp2[pos2] = random.randint(0, app.processor_number - 1)
                temp.append(temp1)
                temp.append(temp2)
                temp = self.create_population(app, temp)
                if temp[0].fitness <= temp[1].fitness:
                    newpopulation.append(temp[0])
                else:
                    newpopulation.append(temp[1])
            else:
                newpopulation.append(p)
        return newpopulation

    def RscLoadAdjust(self, pop_size, app, population):
        for i in range(pop_size):
            ft = [0, 0, 0, 0, 0, 0]
            for j in range(app.tasknum):
                ID = population[i].prossor_sequence[j].id - 1
                ans = population[i].scheduling_list.list[population[i].tsk_sequence[j]].running_span.finish_time
                if ft[ID] < ans:
                    ft[ID] = ans
            lb = population[i].makespan - min(ft)
            population[i].lb = lb
            population[i].ft = ft
        population.sort(key=lambda seq: seq.lb)
        for i in range(pop_size // 2, pop_size):

            bigprossor = population[i].ft.index(max(population[i].ft))

            dex = []
            for j in range(app.tasknum):

                if population[i].chromosome[j] == bigprossor:
                    dex.append(j)

            chro = population[i].chromosome.copy()
            ran = random.randint(0, app.processor_number - 1)
            if ran == bigprossor:
                ran = random.randint(0, app.processor_number - 1)
            chro[dex[random.randint(0, len(dex) - 1)]] = ran
            new_chr = self.create_population(app, [chro])
            if new_chr[0].fitness < population[i].fitness:
                population[i] = new_chr[0]
        return population
