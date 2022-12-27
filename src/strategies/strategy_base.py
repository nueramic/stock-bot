from ..structures.st_strategies import StrategyResponse

class BaseStrategy:
    """
    Базовый класс стратегии. При создании экземпляра класса, в качестве аргументов передаются:
    Необходимые параметры для работы конкретной стратегии.
    """

    def __init__(self, *args, **kwargs):
        """
        :param args:
        :param kwargs:
        """

    def get_decision(self, *args, **kwargs) -> Decision:
        """
        Метод, который возвращает решение стратегии.
        :param args:
        :param kwargs:
        :return: Decision
        """
        raise NotImplementedError