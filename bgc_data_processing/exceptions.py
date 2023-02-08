class VariableInstantiationError(Exception):
    """Exception class to raise when instantiating variables."""

    pass


class CSVLoadingError(Exception):
    """Exception class to raise when loading CSV files."""

    pass


class NetCDFLoadingError(Exception):
    """Exception class to raise when loading nc files."""

    pass
