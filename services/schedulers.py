from abc import ABC, abstractmethod

from domain_models.input_data import InputData
from domain_models.schedule import Schedule
from domain_models.schedule import DispatchDecision
import itertools
import random
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re
import random
from ortools.linear_solver import pywraplp
import copy



class Scheduler(ABC):
    """
    This is an Abstract Base Class (ABC): it simply defines the base constructor and some public methods for
    all its children classes.
    You do not need to change anything in this class.
    """
    def __init__(self, input_data: InputData):
        self._input_data = input_data

    @abstractmethod
    def schedule(self) -> Schedule:
        raise NotImplementedError


class LegacyScheduler(Scheduler):

##    @classmethod
    def possible_machines(self,machines,recipe):
        available_machines =[]
        for machine in machines:
            if recipe in list(machine.processing_time_by_recipe.keys()):
                available_machines.append([machine.name,float(machine.processing_time_by_recipe[recipe])])
        return available_machines
        
    
    def schedule(self) -> Schedule:

        sort_name = sorted(self._input_data.wafers, key=lambda x: x.name)
        sort_prior= sorted(sort_name, key=lambda x: x.priority,reverse=True)
        self._input_data.wafers = sort_prior
        
        
        #Creating a dictionary of last updated available times 
        avail_times={} #List of [machine, next_available_time]
        output_list=[] #List of [wafer,machine,start_time,end_time]

        dispatch_list=[]
        for machine in self._input_data.machines:

            avail_times[machine.name]=0
            

        for wafer in self._input_data.wafers:
            machines_available =self.possible_machines(self._input_data.machines,wafer.recipe)

            for machine in machines_available:
                machine.append(avail_times[machine[0]])
            machines_available = sorted(machines_available, key=lambda x: (x[2],x[0]))

            output_list.append([wafer,wafer.priority,machines_available[0][0],machines_available[0][2],machines_available[0][2]+float(machines_available[0][1])])
            avail_times[machines_available[0][0]]+=float(machines_available[0][1])
            dispatch_list.append(DispatchDecision(wafer.name,machines_available[0][0],machines_available[0][2],machines_available[0][2]+float(machines_available[0][1])))

        leg_sched=Schedule(output_list)
        return leg_sched
            
#Operational Improvement - Choosing the machine with the fastest processing times if multiple machines are available
class BetterScheduler(LegacyScheduler):
    def schedule(self) -> Schedule:
        sort_name = sorted(self._input_data.wafers, key=lambda x: x.name)
        sort_prior= sorted(sort_name, key=lambda x: x.priority,reverse=True)
        self._input_data.wafers = sort_prior
        
        
        #Creating a dictionary of last updated available times 
        avail_times={} #List of [machine, next_available_time]
        output_list=[] #List of [wafer,machine,start_time,end_time]

        dispatch_list=[]
        for machine in self._input_data.machines:

            avail_times[machine.name]=0
            

        for wafer in self._input_data.wafers:
            machines_available =self.possible_machines(self._input_data.machines,wafer.recipe)

            for machine in machines_available:
                machine.append(avail_times[machine[0]])
            machines_available = sorted(machines_available, key=lambda x: (x[2],x[1],x[0]))

            output_list.append([wafer,wafer.priority,machines_available[0][0],machines_available[0][2],machines_available[0][2]+float(machines_available[0][1])])
            avail_times[machines_available[0][0]]+=float(machines_available[0][1])
            dispatch_list.append(DispatchDecision(wafer.name,machines_available[0][0],machines_available[0][2],machines_available[0][2]+float(machines_available[0][1])))

        op_sched=Schedule(output_list)

        return op_sched



#MILP Formulation
class BetterScheduler2(Scheduler):
    def schedule(self) -> Schedule:
##        print(self._input_data.wafers)
        wafer_data = pd.read_csv('data\wafers.csv')
        wafer_data['job_num']=range(len(wafer_data))
        machine_data = pd.read_csv('data\machines_recipes.csv')

        wafer_data['weight'] = np.where(wafer_data['priority']=='red', 1,
                           np.where(wafer_data['priority']=='orange', 0.5,
                           np.where(wafer_data['priority']=='yellow', 0.1, 0)))

        demand_count=dict(wafer_data.value_counts("recipe"))
        recipe_dict ={k: g["recipe"].tolist() for k,g in machine_data.groupby("machine")}



        #Calculating maximum number of positions in Machines
        #Maximum number of positions = recipes a machine can process * number of products with recipe
        machines=[]
        machine_slots={}
        total_slots =0
        for machine in recipe_dict:
            machines.append(machine)
            machine_slots[machine]=0
            for recipe in recipe_dict[machine]:
                machine_slots[machine]+=demand_count[recipe]
                total_slots+=demand_count[recipe]
##        print (machine_slots)
##        print ("Total Slots - ",total_slots)
##        print("Machines - ", machines)



        #Tasks available to schedule in each machine
        machine_candidates={}
        for machine in machines:
            machine_candidates[machine]=[]
            
        for machine in machines:
            for wafer in wafer_data['name']:
                recipe=wafer_data.loc[wafer_data['name'] == wafer,'recipe'].iloc[0]
                if recipe in recipe_dict[machine]:
                    machine_candidates[machine].append(wafer_data.loc[wafer_data['name'] == wafer,'job_num'].iloc[0])


        job_count=len(wafer_data)
        machine_count = len(machines)


        #DECISION VARIABLES
        #y_var= whether to schedule wafer a wafer in a specific position in a machine (Binary)
        #completion_var = completion time of each position in a machine
        solver =pywraplp.Solver.CreateSolver('SCIP')

        infinity =solver.infinity()

##        y_var ={}
##        for i in range(machine_count):
##            y_var[machines[i]]=[solver.IntVar(0,1,'y[%d][%d]' %((i+1),(j+1))) for j in range(machine_slots[machines[i]])]

        y_var ={}
        i=0
        for machine in machines:
            for pos in range(machine_slots[machine]):
                for job in machine_candidates[machine]:
                    # y_var[machine][pos][jobs]=solver.IntVar(0,1,'y[%d][%d][%d]' %((machine),(pos),(job)))
                    y_var[i]=solver.IntVar(0,1,'y[%s][%d][%d]' %((machine),(pos),(job)))
                    i+=1

                # y_var[machines[i]]=[solver.IntVar(0,1,'y[%d][%d]' %((i+1),(j+1))) for j in range(machine_slots[machines[i]])]

        completion_var ={}
        for i in range(machine_count):
            completion_var[machines[i]]=[solver.NumVar(0,infinity,'c[%d][%d]' %((i),(j))) for j in range(machine_slots[machines[i]])]


        #CONSTRAINTS
        # Constraint 1 - Each position in each machine only 1 job
        for machine in machines:
            for pos in range(machine_slots[machine]):
                expr=[]
                for var in y_var:
                    pattern = r'[\[\]]'
                    result = re.split(pattern, str(y_var[var]))
                    # print (result)
                    if result[1]== machine and result[3]== str(pos):
                        expr.append(y_var[var])
                
                solver.Add(sum(expr) <= 1)
                
                    
                # expr =[y[machine][pos][job] for job in range(len(machine_candidates[machines[machine]]))]
                # solver.Add(sum(expr) <= 1)

        # Constraint 2 - Each job needs one and only in 1 position
        for job in range(job_count):
            expr=[]
            for var in y_var:
                pattern = r'[\[\]]'
                result = re.split(pattern, str(y_var[var]))
                if result[5]== str(job):
                    expr.append(y_var[var])
            # print(expr)
            solver.Add(sum(expr) <= 1)
            solver.Add(sum(expr) >= 1)

        #Constraint 3 - Completion time first position in each machine 
        for machine in machines:
            expr=[]
            for var in y_var:
                pattern = r'[\[\]]'
                result = re.split(pattern, str(y_var[var]))
                if result[3]== str(0) and result[1]== machine: #first_position
                    machine_allocated=result[1]
                    job=int(result[5])
                    recipe=wafer_data.loc[(wafer_data['job_num'] == job),'recipe'].iloc[0]
                    processing_time=machine_data.loc[(machine_data['machine'] == machine_allocated) & (machine_data['recipe'] == recipe),'processing_time'].iloc[0]
                    expr.append(y_var[var]*processing_time)
                # print(expr)
            solver.Add(sum(expr) <= completion_var[machine][0])
            solver.Add(sum(expr) >= completion_var[machine][0])

        #Constraint 4- Completion Time of every other position
        for machine in machines:
            for pos in range(1,machine_slots[machine]):
                expr=[]
                for var in y_var:
                    pattern = r'[\[\]]'
                    result = re.split(pattern, str(y_var[var]))
                    if result[1]== machine and result[3]== str(pos):
                        machine_allocated=result[1]
                        job=int(result[5])
                        recipe=wafer_data.loc[(wafer_data['job_num'] == job),'recipe'].iloc[0]
                        processing_time=machine_data.loc[(machine_data['machine'] == machine_allocated) & (machine_data['recipe'] == recipe),'processing_time'].iloc[0]
                        expr.append(y_var[var]*processing_time)
                solver.Add(completion_var[machine][pos] >= completion_var[machine][pos-1] + sum(expr))


        ##Objective function - We are trying to minimize the sum of the completion time of each position in each machine
        objective_terms=[]
        for machine in machines:
            for pos in range(machine_slots[machine]):
                completion_time= completion_var[machine][pos]
                expr=[]
                objective_terms.append(completion_var[machine][pos])
                # print(objective_terms)
                
        solver.Minimize(solver.Sum(objective_terms))
        status =solver.Solve()


        ##Parsing Optimal Solution
        ##The optimal solution only tells us which machines to schedule a wafer. The order in which it is to be scheduled is determined after using a greedy approach.
        max_completion=[]
        for machine in machines:
            maxi=0 
            for pos in range(machine_slots[machine]):
                if completion_var[machine][pos].solution_value() > maxi:
                    maxi=completion_var[machine][pos].solution_value()
            max_completion.append(maxi)


        machine_tasks={}
        for machine in machines:
            machine_tasks[machine]=[]

        for machine in machines:
            for var in y_var:
                pattern = r'[\[\]]'
                result = re.split(pattern, str(y_var[var]))
                if result[1]== machine and y_var[var].solution_value()==1:
                    # print(result[5])
                    task_selected=int(result[5])
                    priority = wafer_data.loc[(wafer_data['job_num'] == task_selected),'weight'].iloc[0]
                    recipe=wafer_data.loc[(wafer_data['job_num'] == task_selected),'recipe'].iloc[0]
                    processing_time=machine_data.loc[(machine_data['machine'] == machine) & (machine_data['recipe'] == recipe),'processing_time'].iloc[0]
                    machine_tasks[machine].append([task_selected,priority,processing_time,priority*processing_time])

        #Reordering scheduling within each machine - Based on Priority
        pwct=0
        output_list=[]
        for machine in machines:
            #Sorting by Priority
            machine_tasks[machine]=sorted(machine_tasks[machine], key=lambda x: x[1],reverse=True)
            start_time =0
            for tasks in machine_tasks[machine]:
                tasks.append(start_time)
                tasks.append(start_time+tasks[2])
                task_name=wafer_data.loc[(wafer_data['job_num'] == tasks[0]),'name'].iloc[0]
                output_list.append([task_name,tasks[1],machine,start_time,start_time+tasks[2]])
                start_time+=tasks[2]
                pwct+=(start_time*tasks[1])

        for decision in range(len(output_list)):
            for wafer in self._input_data.wafers:
                if wafer.name==output_list[decision][0]:
                    output_list[decision][0]=wafer
                


        mip_sched=Schedule(output_list)
        return mip_sched
        




    

#Genetic Algorithm
class BetterScheduler3(BetterScheduler):

    def objective(self,selected_machines):
        wafer_list=self._input_data.wafers
        machines=self._input_data.machines
        machine_tasks_ordered={}

        for machine in self._input_data.machines:
            machine_tasks_ordered[machine]=[]

        output_list=[]
        for i in range(len(wafer_list)):
            machine_allocated=selected_machines[i]
         
            try:
                machine_dict =self._input_data.machines[machine_allocated].processing_time_by_recipe
                time_2_process=float(machine_dict[wafer_list[i].recipe])
            except:
                time_2_process= 10000 #penalty - for mutation
            output_list.append([wafer_list[i],wafer_list[i].priority,self._input_data.machines[machine_allocated],time_2_process])

        output_list = sorted(output_list, key=lambda x: (x[2].name,x[1]),reverse=True)
        for task in output_list:
            machine_tasks_ordered[task[2]].append([task[0],task[1],task[3]])

        #Adding Start/End Time
        pwct=0
        for machine in machines:
            start_time =0
            tasks=copy.deepcopy(machine_tasks_ordered[machine])
            for task in range(len(tasks)):
                end_time=start_time+tasks[task][2]
                machine_tasks_ordered[machine][task].append(start_time)
                machine_tasks_ordered[machine][task].append(end_time)
                pwct+=end_time*tasks[task][1]
                start_time=end_time

        return pwct

    # tournament selection
    def selection(self,pop, scores, k=3):
        # first random selection
        selection_ix = random.randint(0,len(pop)-1)
        for ix in random.sample(range(0,len(pop)), k-1):
	    # check if better (e.g. perform a tournament)
            if scores[ix]>scores[selection_ix]:
                selection_ix = ix
        
        return pop[selection_ix]

    # crossover two parents for two children
    def crossover(self,p1, p2, r_cross):
        c1,c2=copy.deepcopy(p1),copy.deepcopy(p2)
	
	# checking for crossover
        if random.random()<r_cross:
            # selecting crossover point 
            pt=random.randint(1,len(p1)-2)
            # performing crossover
            c1=p1[:pt]+p2[pt:]
            c2=p2[:pt]+p1[pt:]

        return [c1, c2]

    # mutation operator
    def mutation(self,parent, r_mut):
        for i in range(len(parent)):
            # check for a mutation
            if random.random() < r_mut:
                # Trying another machine
                parent[i] = 1 + parent[i]

            return parent
				
    def schedule(self) -> Schedule:

        wafer_data = pd.read_csv('data\wafers.csv')
        wafer_data['job_num']=range(len(wafer_data))
        machine_data = pd.read_csv('data\machines_recipes.csv')

        wafer_data['weight'] = np.where(wafer_data['priority']=='red', 1,
                           np.where(wafer_data['priority']=='orange', 0.5,
                           np.where(wafer_data['priority']=='yellow', 0.1, 0)))

        recipe_dict ={k: g["recipe"].tolist() for k,g in machine_data.groupby("machine")}

        machines=self._input_data.machines
        wafers=self._input_data.wafers

        machines_eligible={}
        for wafer in wafers:
            machines_eligible[wafer]=[]

        for wafer in wafers:
            for machine in range(len(machines)):
                recipe_possible=recipe_dict[machines[machine].name]
                # recipe_possible=list(machine_data.loc[(machine_data['machine'] == machines[machine]),'recipe'])
                # wafer_recipe=wafer_data.loc[(wafer_data['name'] == wafer),'recipe'].iloc[0]

                if wafer.recipe in recipe_possible:
                    machines_eligible[wafer].append(machine)

##        for task in machines_eligible:
##            print(task,machines_eligible[task])
        
        pop_size= 10
        n_iter=20
        r_cross=0.8
        r_mut=0.01


        #Generating Initial Population
        pop =[]
        for parent_num in range(pop_size):
            parent=[]
            for wafer in wafers:
                machine_allocated=random.choice(machines_eligible[wafer])
                parent.append(machine_allocated)
            pop.append(parent)

        #Evolution begins
        best, best_eval = pop[0], self.objective(pop[0])

        for gen in range(n_iter):
            scores = [self.objective(c) for c in pop]

            # check for new best solution
            for i in range(pop_size):
                if scores[i] < best_eval:
                    best, best_eval = pop[i], scores[i]
                    
            # select pop_size number of parents
            selected = [self.selection(pop,scores) for i in range(pop_size)]

            children = list()
            for i in range(0, pop_size, 2):
                p1, p2 = selected[i], selected[i+1]
                for c in self.crossover(p1, p2, r_cross):
##                    c=self.mutation(c, r_mut)
                    children.append(c)      

            pop = children
        ### ---------------Genetic Algorithm Ends--------------------------

            
        selected_machines=best
        print ('PWCT - ', best_eval)
        return 0
        

##        wafer_list=self._input_data.wafers
##        machines=self._input_data.machines
##
##        
##        machine_tasks_ordered={}
##        for machine in machines:
##            machine_tasks_ordered[machine]=[]

##        output_list=[]
##        for i in range(len(wafer_list)):
##            machine_allocated=selected_machines[i]
##
##            machine_dict =self._input_data.machines[machine_allocated].processing_time_by_recipe
####                print (machine_dict)
##            time_2_process=float(machine_dict[wafer_list[i].recipe])
##             
####            try:
####                machine_dict =self._input_data.machines[machine_allocated].processing_time_by_recipe
######                print (machine_dict)
####                time_2_process=float(machine_dict[wafer_list[i].recipe])
####            except:
####                time_2_process= 10000 #penalty - for mutation
##
####            print(self._input_data.machines[machine_allocated])
##            output_list.append([wafer_list[i],wafer_list[i].priority,machines[machine_allocated],time_2_process])
##
##        output_list = sorted(output_list, key=lambda x: (x[2].name,x[1]),reverse=True)
##        for task in output_list:
##            machine_tasks_ordered[task[2]].append([task[0],task[1],task[3]])
##
##
##        #Adding Start/End Time
##        for machine in machines:
##            start_time =0
##            tasks=copy.deepcopy(machine_tasks_ordered[machine])
##            for task in range(len(tasks)):
##                end_time=start_time+tasks[task][2]
##                machine_tasks_ordered[machine][task].append(start_time)
##                machine_tasks_ordered[machine][task].append(end_time)
##
##                start_time=end_time
##
####        for machine in machine_tasks_ordered:
####            print (machine, machine_tasks_ordered[machine])
##
##        output=[]
##        for machine in machine_tasks_ordered:
##            tasks=machine_tasks_ordered[machine]
##            for task in tasks:
####                print(task)
##                output.append([task[0],task[1],machine,task[3],task[4]])
####        print(len(output))
####        print(output)
##        gen_sched=Schedule(output)
##
##        return gen_sched





