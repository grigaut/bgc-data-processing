"""Specific exceptions."""


class VariableInstantiationError(Exception):
    """Exception class to raise when instantiating variables."""


class CSVLoadingError(Exception):
    """Exception class to raise when loading CSV files."""


class NetCDFLoadingError(Exception):
    """Exception class to raise when loading NetCDF files."""


class ABFileLoadingError(Exception):
    """Exception class to raise when loading NetCDF files."""


class IncorrectVariableNameError(Exception):
    """Exception raised when trying to access a variable using an incorrect name."""


class DuplicatedVariableNameError(Exception):
    """Exception raised when trying to add a variable with an already used name."""


class IncompatibleVariableSetsError(Exception):
    """Exception raised when performing operation on incompatible variable sets."""


class IncompatibleCategoriesError(Exception):
    """Exception raised when performing operation on incompatible data categories."""


class DifferentSliceOriginError(Exception):
    """Exception raised when performing operation ons torers with differents storers."""
