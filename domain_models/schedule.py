from datetime import datetime
import csv
from domain_models.machine import Machine
from domain_models.wafer import Wafer


class DispatchDecision:
    def __init__(
        self,
        wafer: Wafer,
        machine: Machine,
        start: datetime,
        end: datetime,
    ):
        self.wafer = wafer
        self.machine = machine
        self.start = start
        self.end = end


class Schedule:
##    def __init__(self, dispatch_decisions: list[DispatchDecision]):
    def __init__(self, dispatch_decisions):
        self.dispatch_decisions = dispatch_decisions

    @property
    def makespan(self) -> float:
        """

        Returns
        -------
        float : Schedule's makespan in hours
        """
        end_time=[]
        for decision in self.dispatch_decisions:
            end_time.append(decision[4])

        make_span=float(max(end_time))
        return make_span
##        raise NotImplementedError

    @property
    def priority_weighted_cycle_time(self) -> float:
        """

        Returns
        -------
        float : Schedule's priority-weighted cycle times summed for all wafers.
        """
        pwct=0
        for decision in self.dispatch_decisions:
            pwct+=(decision[0].priority)*(decision[4])

        return pwct

    def to_csv(self, output_file: str) -> None:
        """
        Writes schedule to a csv file.

        Parameters
        ----------
        output_file: str
            The output csv file path

        Returns
        -------

        """

        with open(output_file, 'w', newline='') as file:
            writer = csv.writer(file)
             
            writer.writerow(["Wafer", "Priority", "Machine","Start Time","End Time"])
            for decision in self.dispatch_decisions:
                writer.writerow([decision[0].name, decision[1],decision[2], decision[3],decision[4]])

        
##        raise NotImplementedError
