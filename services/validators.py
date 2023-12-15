from abc import ABC, abstractmethod

from domain_models.input_data import InputData
from domain_models.schedule import Schedule


class ScheduleValidator(ABC):
    """
    This is an Abstract Base Class (ABC): it simply defines the base constructor and some public methods for
    all its children classes.
    You do not need to change anything in this class.
    """
    def __init__(self, input_data: InputData, schedule: Schedule):
        self._input_data = input_data
        self._schedule = schedule

    @abstractmethod
    def validate(self):
        raise NotImplementedError


class AllWafersHaveBeenScheduled(ScheduleValidator):
    def validate(self) -> bool:
        """
        Checks that all wafers have been scheduled.
        """
        wafers = self._input_data.wafers
        machines = self._input_data.machines
        decisions=self._schedule.dispatch_decisions #List of decisions

        not_scheduled=0
        for wafer in wafers:
            found=0
            for decision in decisions:
                if decision[0]==wafer:
                    found+=1
            if found>1:
                print("Wafers scheduled more than once - ",wafer)
            elif found==0:
                not_scheduled+=1
            else:
                pass
        if not_scheduled >0:
            return False
        else:
            return True
                
##        print(wafers)
##        return True
##        raise NotImplementedError


class AllWafersAreOnCompatibleMachines(ScheduleValidator):

    def possible_machines(self,machines,recipe):
        available_machines =[]
        for machine in machines:
            if recipe in list(machine.processing_time_by_recipe.keys()):
                available_machines.append(machine.name)
        return available_machines
    
    def validate(self) -> bool:
        """
        Checks that each wafer has been scheduled on a machine with a compatible recipe.
        """
        wafers = self._input_data.wafers
        machines = self._input_data.machines
        decisions=self._schedule.dispatch_decisions #List of decisions

        compatibility_violation=0
        for decision in decisions:
            machine_allocated=decision[2]
            machines_allowed=self.possible_machines(machines,decision[0].recipe)

            if machine_allocated not in machines_allowed:
                compatibility_violation+=1

        if compatibility_violation == 0:
            return True
        else:
            return False
            
        return True
##        raise NotImplementedError


class NoOverlapsOnSameMachine(ScheduleValidator):

    def validate(self) -> bool:
        """
        Checks that there are no overlapping wafers scheduled on the same machine.
        """

        wafers = self._input_data.wafers
        machines = self._input_data.machines
        decisions = self._schedule.dispatch_decisions #List of decisions

        overlap_machines=[]
        for machine in machines:
            machine_sched=[]
            for decision in decisions:
                if decision[2]==machine.name:
                    machine_sched.append(decision)
                    
            overlap=0
            for task in range(1,len(machine_sched)):
                if machine_sched[task][3]<machine_sched[task-1][4]:
                    overlap+=1
            overlap_machines.append(overlap)

        machine_count=0
        for overlap in overlap_machines:
            if overlap>0:
                machine_count+=1

        if machine_count==0:
            return True
        else:
            print ("Number of machines with overlap - ",machine_count)
            return False

##        raise NotImplementedError


class ScheduleChecker:
    def __init__(self, input_data: InputData, schedule: Schedule):
        self._input_data = input_data
        self._schedule = schedule
        self._validator_classes = [
            AllWafersHaveBeenScheduled,
            AllWafersAreOnCompatibleMachines,
            NoOverlapsOnSameMachine,
        ]

    def check(self) -> None:
        for validator_cls in self._validator_classes:
            is_valid = validator_cls(
                schedule=self._schedule, input_data=self._input_data
            ).validate()
            print(f"{validator_cls.__name__:45s} : {'PASS' if is_valid else 'FAIL'}")
