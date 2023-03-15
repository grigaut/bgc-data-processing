"""Functions, classes or decorator useful for development."""
import warnings


def temporarywarning(message: str = ""):
    def inner(func: callable):
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__name__} is a temporary implementation. {message}",
                FutureWarning,
            )
            return func(*args, **kwargs)

        return wrapper

    return inner
