from domain_models.machine import Machine
from domain_models.wafer import Wafer
from services.csv_reader import CsvReader


class InputData:
    def __init__(self, wafers: list[Wafer], machines: list[Machine]):
        self.wafers = wafers
        self.machines = machines

    @classmethod
    def from_csv(cls, path: str):
        csv_reader = CsvReader(path=path)
        wafers = csv_reader.get_wafers()
        machines = csv_reader.get_machines()
        return InputData(wafers=wafers, machines=machines)
