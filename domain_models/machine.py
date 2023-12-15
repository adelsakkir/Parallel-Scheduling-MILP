from datetime import timedelta

from domain_models.recipe import RecipeId


class Machine:
    def __init__(
        self,
        name: str,
        processing_time_by_recipe: dict[RecipeId, timedelta],
    ):
        self.name = name
        self.processing_time_by_recipe = processing_time_by_recipe

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name})"
