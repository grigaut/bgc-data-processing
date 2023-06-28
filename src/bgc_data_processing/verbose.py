"""Verbose decorator."""

from functools import wraps


def set_verbose_level(level: int) -> None:
    """Instanciate the Verbose singleton to a given value.

    Parameters
    ----------
    level : int
        Verbose level.
    """
    Verbose(level=level)


class Verbose:
    """Verbose Singleton class."""

    _instance = None
    max_allowed: int = 2
    min_allowed: int = 0

    def __new__(cls, level: int = 1) -> "Verbose":
        """Instanciate new verbose singleton.

        Create an instance if there is no instance existing.
        Otherwise, return the existing one.

        Parameters
        ----------
        level : int, optional
            Verbose level, the higher the more verbose., by default 1

        Returns
        -------
        Verbose
            Verbose singleton
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Put any initialization here.
            cls.level = level
        return cls._instance

    @property
    def level(self) -> int:
        """Verbose level."""
        return self._level

    @level.setter
    def level(self, level) -> None:
        assert isinstance(level, int), "self.level must be an instance of int"
        self._level = level


def with_verbose(trigger_threshold: int, message: str):
    """_summary_.

    Parameters
    ----------
    trigger_threshold : int
        _description_
    message : str
        _description_
    """

    def verbose_wrapper(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            assert isinstance(trigger_threshold, int), "ff"
            verbose = Verbose()
            level = max(
                verbose.min_allowed,
                min(trigger_threshold, verbose.max_allowed),
            )
            if verbose.level > level:
                offset = "".join(["\t"] * level)
                print(f"{offset}{message.format(**kwargs)}")
            return func(*args, **kwargs)

        return wrapper

    return verbose_wrapper
