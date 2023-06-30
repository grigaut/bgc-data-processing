"""Verbose decorator."""

from functools import wraps


def set_verbose_level(level: int) -> None:
    """Instanciate the Verbose singleton to a given value.

    Parameters
    ----------
    level : int
        Verbose level.
    """
    verbose = Verbose()
    verbose.level = level


class Verbose:
    """Verbose Singleton class."""

    _instance = None
    max_allowed: int = 2
    min_allowed: int = 0

    def __new__(cls) -> "Verbose":
        """Instanciate new verbose singleton.

        Create an instance if there is no instance existing.
        Otherwise, return the existing one.

        Returns
        -------
        Verbose
            Verbose singleton
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
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
    """Display verbose on the function call.

    One must keep in mind that the message is displayed only if the verbose
    level is STRICTLY greater than the trigger_threshold.

    In order to use a placeholder to insert values in the message use square brackets
    ('[' and ']').
    However, keep in mind that for the placeholder to work, one must
    the name of the parameter in the function call.

    For example, with:

    >>> @with_verbose(trigger_threshold=0, message="Input with a=[a]")
    >>> def func(a: int) -> None:
    >>>     print(a)

    We can have the following results depending on how 'func' is called:

    >>> func(a=3)
    ... Input with a=3
    ... 3

    Or

    >>> func(3)
    ... Input with a=[a]
    ... 3

    Parameters
    ----------
    trigger_threshold : int
        Level to use as trigger for verbose display.
        Example: if trigger_level = 1 -> message is displayed if
        the global verbose level is striclty greater than 1.
    message : str
        Message to display.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not isinstance(trigger_threshold, int):
                error_msg = "Trigger threshold must be an integer"
                raise TypeError(error_msg)
            verbose = Verbose()
            threshold_or_max = min(trigger_threshold, verbose.max_allowed)
            level = max(verbose.min_allowed, threshold_or_max)
            content = message
            if verbose.level > level:
                # Adjust indentation
                offset = "".join(["\t"] * level)
                # Replace placeholders
                for key, value in kwargs.items():
                    content = content.replace("[" + key + "]", str(value))
                    # verbose
                print(f"{offset}{content}")
            return func(*args, **kwargs)

        return wrapper

    return decorator
