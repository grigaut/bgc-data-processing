"""Specific exceptions."""


class VariableInstantiationError(Exception):
    """Exception class to raise when instantiating variables."""


class CSVLoadingError(Exception):
    """Exception class to raise when loading CSV files."""


class NetCDFLoadingError(Exception):
    """Exception class to raise when loading NetCDF files."""


class ABFileLoadingError(Exception):
    """Exception class to raise when loading NetCDF files."""
