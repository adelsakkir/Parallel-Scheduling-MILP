from domain_models.input_data import InputData
from services.schedulers import LegacyScheduler, BetterScheduler, BetterScheduler2,BetterScheduler3
from services.validators import ScheduleChecker
import ortools
import pip
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re


if __name__ == "__main__":

    input_data = InputData.from_csv(path="data/")
    

    print("-- Legacy Scheduler ---------------")
    old_schedule = LegacyScheduler(input_data=input_data).schedule()
    ScheduleChecker(input_data=input_data, schedule=old_schedule).check()
    print(f"Makespan                     : {old_schedule.makespan:,.2f} hours")
    print(
        f"Priority-weighted cycle time : {old_schedule.priority_weighted_cycle_time:,.2f} weighted hours"
    )
    old_schedule.to_csv(output_file="output/1_old_schedule.csv")



    

    print("\n\n-- Better Scheduler ---------------")
    print("Choosing the machine with the least processing time from available machines")
    op_schedule = BetterScheduler(input_data=input_data).schedule()

    ScheduleChecker(input_data=input_data, schedule=op_schedule).check()
    print(f"Makespan                     : {op_schedule.makespan:,.2f} hours")
    print(
        f"Priority-weighted cycle time : {op_schedule.priority_weighted_cycle_time:,.2f} weighted hours"
    )
    op_schedule.to_csv(output_file="output/2_OP_Improv_schedule.csv")



    print("\n\n-- Better Scheduler 2 ---------------")
    print("MILP Formulation")
    mip_schedule = BetterScheduler2(input_data=input_data).schedule()

    
    ScheduleChecker(input_data=input_data, schedule=mip_schedule).check()
    print(f"Makespan                     : {mip_schedule.makespan:,.2f} hours")
    print(
        f"Priority-weighted cycle time : {mip_schedule.priority_weighted_cycle_time:,.2f} weighted hours"
    )
    mip_schedule.to_csv(output_file="output/3_MIP_schedule.csv")





    print("\n\n-- Better Scheduler 3---------------")
    print("Genetic Algorithm")
    gen_schedule = BetterScheduler3(input_data=input_data).schedule()
    print("The crossover step in the genetic algorithm implementation does not produce better solutions than the initial parent population")
    
##    ScheduleChecker(input_data=input_data, schedule=gen_schedule).check()
##    print(f"Makespan                  : {gen_schedule.makespan:,.2f} hours")
##    print(
##        f"Priority-weighted cycle time : {gen_schedule.priority_weighted_cycle_time:,.2f} hours"
##    )
##    gen_schedule.to_csv(output_file="output/4_Genetic_Algo_schedule.csv")

    print("\n-- Additional Comments---------------- ")
    print("""\nThank you for the problem, I loved working on it.
I have a module in Reinforcement Learning next semester. I would love to see how this can be modelled with it.
Additionally, implementation of evolutionary methods to find the best order of schedule within each machine after getting a solution from the MILP could be explored.

Thanks, Adel""")


    


