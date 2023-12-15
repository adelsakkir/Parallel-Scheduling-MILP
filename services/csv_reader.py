from domain_models.machine import Machine
from domain_models.wafer import Wafer
import pandas as pd
import csv


class CsvReader:
    def __init__(self, path: str):
        """

        Parameters
        ----------
        path: str
            The directory path containing the two csv files to be read.
        """
        self._path = path

    def get_wafers(self): #-> list[Wafer]:
        """

        Reads in "wafers.csv" and returns a list of `Wafer` objects.
        -------
        wafers : list[Wafer]
            The list of wafers
        """

        wafers_data = open(self._path+'wafers.csv')
        csvreader = csv.reader(wafers_data)
        rows = []
        for row in csvreader:
            rows.append(row)
        rows=rows[1:]

        Wafer_list=[]
        for row in rows:
            if row[1]=="red":
                prior_weight=1
            elif row[1]=="orange":
                prior_weight=0.5
            else:
                prior_weight=0.1
            wafer_obj=Wafer(row[0],prior_weight,row[2])
            Wafer_list.append(wafer_obj)

        return Wafer_list

        

    def get_machines(self): #-> list[Machine]:
        """

        Reads in "machines_recipes.csv" and returns a list of `Machine` objects.
        -------
        machines : list[Machine]
            The list of machines

        """
        machine_data = open(self._path+'machines_recipes.csv')
        csvreader = csv.reader(machine_data)
        rows = []
        for row in csvreader:
            rows.append(row)
        rows=rows[1:] # removing header

        #getting unique machine names
        machine_names=[]
        for row in rows:
            if row[0] not in machine_names:
                machine_names.append(row[0])

        #Creating a list of machine objects
        Machine_list=[]
        for machine in machine_names:
            process_dict={}
            for row in rows:
                if row[0] == machine:
                    process_dict[row[1]]=row[2]

            machine_obj=Machine(machine,process_dict)
            Machine_list.append(machine_obj)

        return Machine_list
