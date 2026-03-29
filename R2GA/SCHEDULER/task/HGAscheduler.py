


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


class HGAScheduler(Scheduler):

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
            crossover_chromosomes = self.crossover(pop_size, app, half_population)
            mutation_chromosomes = self.mutate(app, crossover_chromosomes, MutationRate)
            population = population[:Elitepop]
            population.extend(mutation_chromosomes)
            population = self.RscLoadAdjust(pop_size, app, population)
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

        if sign <= 10:
            complete_time = {}
            lists = elite_sequence.scheduling_list
            for i in elite_sequence.tsk_sequence:
                start_time = lists.list[i].running_span.start_time
                finish_time = lists.list[i].running_span.finish_time
                span = lists.list[i].running_span.span
                id = (elite_sequence.tsk_sequence[elite_sequence.tsk_sequence.index(i)].id,
                      elite_sequence.prossor_sequence[elite_sequence.tsk_sequence.index(i)].id)
                complete_time[id] = (start_time, finish_time, span)

            colors = {}
            col = 0
            for i in range(1, app.tasknum + 1):
                colors[i] = col
                col += 1
                if col > 7:
                    col = 0
            e = 255
            color = [(144/e, 201/e, 231/e), (33/e, 158/e, 188/e), (19/e, 103/e, 131/e),
                     (21/e, 151/e, 165/e), (254/e, 183/e, 5/e), (243/e, 162/e, 97/e),
                     (250/e, 134/e, 0/e), (233/e, 196/e, 107/e)]
            for k, v in complete_time.items():
                plt.barh(y=k[1], width=v[2], left=v[0], edgecolor="black", color=color[colors[k[0]]])
                plt.text(v[0] + 0.2, k[1], 't' + str(k[0] - 1), fontsize=10, verticalalignment="center")

            my_y_ticks = np.arange(1, app.processor_number + 1, 1)

            plt.yticks(my_y_ticks)
            plt.title("Gantt chart")
            plt.xlabel("makespan")
            plt.ylabel("processor")
            plt.vlines(elite_sequence.makespan, 0, app.processor_number + 1, colors='black',
                       label="makespan=" + str(int(elite_sequence.makespan)))
            plt.legend(bbox_to_anchor=(0.68, 1.01), loc=3, borderaxespad=0)

            plt.gca().margins(x=0)
            plt.gcf().canvas.draw()

            maxsize = 100
            m = 0.2
            N = len(complete_time)
            s = maxsize / plt.gcf().dpi * N + 2 * m
            margin = m / plt.gcf().get_size_inches()[0]

            plt.gcf().subplots_adjust(left=margin, right=1. - margin)
            plt.gcf().set_size_inches(s, plt.gcf().get_size_inches()[1])

            plt.show()
        return makespan, cost

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
        population.sort(key=lambda seq: seq.makespan)
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
            temp_l.sort(key=lambda seq: seq.makespan)
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
                if temp[0].makespan <= temp[1].makespan:
                    newpopulation.append(temp[0])
                else:
                    newpopulation.append(temp[1])
            else:
                newpopulation.append(p)
        return newpopulation
        pass

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
            if new_chr[0].makespan < population[i].makespan:
                population[i] = new_chr[0]
        return population