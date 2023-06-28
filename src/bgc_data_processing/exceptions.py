"""Specific exceptions."""

from pathlib import Path


# Variables Related Errors
class VariableInstantiationError(Exception):
    """Exception class to raise when instantiating variables."""


class IncorrectVariableNameError(Exception):
    """Exception raised when trying to access a variable using an incorrect name."""


class DuplicatedVariableNameError(Exception):
    """Exception raised when trying to add a variable with an already used name."""


class IncompatibleVariableSetsError(Exception):
    """Exception raised when performing operation on incompatible variable sets."""


class FeatureConstructionError(Exception):
    """Exception raised when unsuccessfully trying to build a feature."""


# Loading Related Errors
class CSVLoadingError(Exception):
    """Exception class to raise when loading CSV files."""


class NetCDFLoadingError(Exception):
    """Exception class to raise when loading NetCDF files."""


class ABFileLoadingError(Exception):
    """Exception class to raise when loading NetCDF files."""


class UnsupportedLoadingFormatError(Exception):
    """Exception raised when trying to load data with unsupported format."""

    def __init__(self, file_format: str) -> None:
        error_msg = f"File format: {file_format} can not be loaded."
        super().__init__(error_msg)


# Storer Related Errors
class IncompatibleCategoriesError(Exception):
    """Exception raised when performing operation on incompatible data categories."""


class DifferentSliceOriginError(Exception):
    """Exception raised when performing operation ons torers with differents storers."""


class IncomparableStorersError(Exception):
    """Exception raised when storers with uncomparable properties are compared."""


class ImpossibleSaveError(Exception):
    """Exception raised when it is impossible to save a Storer."""


# Parsing Related Errors
class ImpossibleTypeParsingError(Exception):
    """Exception raised when a TOML parser can not access to a variable's type."""

    def __init__(self, keys: list[str], filepath: Path | str) -> None:
        error_msg = f"Type of {'.'.join(keys)} can't be parsed from {filepath}"
        super().__init__(error_msg)


class InvalidParameterKeyError(Exception):
    """Exception raised when accessing a parsed parameter using an incorrect name."""

    def __init__(self, keys: list[str], filepath: Path | str) -> None:
        error_msg = f"Variable {'.'.join(keys)} does not exist in {filepath}"
        super().__init__(error_msg)


# Comparison Related Errors
class IncompatibleMaskShapeError(Exception):
    """Exception raised when a Mask with an incorrect shape is trying to be set."""

    def __init__(self, correct_shape: tuple, incorrect_shape: tuple) -> None:
        error_msg = (
            f"Mask shape should be {correct_shape}. "
            f"Given mask shape is {incorrect_shape}."
        )
        super().__init__(error_msg)


# Patterns Related Errors
class InvalidDateInputsError(Exception):
    """Exception raised when a DateIntervalPattern is set with invalid dates."""


class InvalidPrecisionError(Exception):
    """Exception raised when a DateIntervalPattern is set with invalid precision."""
