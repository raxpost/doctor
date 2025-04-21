from abc import ABC, abstractmethod

class Language(ABC):
    @abstractmethod
    def fetch_env_vars(self):
        pass
    @abstractmethod
    def fetch_comparisons(self):
        pass