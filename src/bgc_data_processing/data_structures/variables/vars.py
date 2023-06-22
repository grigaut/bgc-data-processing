"""Variables."""

from abc import ABC
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any, ClassVar

import numpy as np

from bgc_data_processing.exceptions import VariableInstantiationError

if TYPE_CHECKING:
    from bgc_data_processing.features import BaseFeature


class BaseVar(ABC):
    """Class to store Meta data on a variable of interest.

    Parameters
    ----------
    name : str
        'Official' name for the variable : name to use when displaying the variable.
    unit : str
        Variable unit (written using the following format:
        [deg_C] for Celsius degree of [kg] for kilograms).
    var_type : str
        Variable type (str, int, datetime...).
        It will be used to convert the data using df[variable].astype(type)
    default: Any
        Default value to set instead of nan., by default np.nan
    name_format: str
        Format to use to save the data name and unit in a csv of txt file.
        , by default "%-15s"
    value_format: str
        Format to use to save the data value in a csv of txt file., by default "%15s"

    Examples
    --------
    >>> var_lat = BaseVar("LATITUDE", "[deg_N]", float, 7, 6, "%-12s", "%12.6f")
    """

    is_feature = False
    exist_in_dset: bool = None

    def __init__(
        self,
        name: str,
        unit: str,
        var_type: str,
        default: Any = np.nan,
        name_format: str = "%-15s",
        value_format: str = "%15s",
    ):
        """Class to store Meta data on a variable of interest.

        Parameters
        ----------
        name : str
            'Official' name for the variable : name to use when displaying the variable.
        unit : str
            Variable unit (written using the following format:
            [deg_C] for Celsius degree of [kg] for kilograms).
        var_type : str
            Variable type (str, int, datetime...).
            It will be used to convert the data using df[variable].astype(type)
        default: Any
            Default value to set instead of nan., by default np.nan
        name_format: str
            Format to use to save the data name and unit in a csv of txt file.
            , by default "%-15s"
        value_format: str
            Format to use to save the data value in a csv/txt file., by default "%15s"

        Examples
        --------
        >>> var_lat = BaseVar("LATITUDE", "[deg_N]", float, 7, 6, "%-12s", "%12.6f")
        """
        self.name = name
        self.unit = unit
        self.type = var_type
        self.default = default
        self.name_format = name_format
        self.value_format = value_format

    def __hash__(self) -> int:
        """Hashing method.

        Returns
        -------
        int
            Hashed object.
        """
        return hash(self.__repr__())

    def __str__(self) -> str:
        """Convert the variable to a string.

        Returns
        -------
        str
            name - unit (type)
        """
        return f"{self.name} - {self.unit} ({self.type})"

    def __repr__(self) -> str:
        """Represent the variable as string.

        Returns
        -------
        str
            name_unit_type
        """
        return f"{self.name}_{self.unit}"

    def __eq__(self, __o: object) -> bool:
        """Test variable equality.

        Parameters
        ----------
        __o : object
            Object to test equality with.

        Returns
        -------
        bool
            True if both are instance of basevar with same representation.
        """
        if isinstance(__o, BaseVar):
            return repr(self) == repr(__o)
        return False

    @property
    def label(self) -> str:
        """Returns the label to use to find the variable data in a dataframe.

        Returns
        -------
        str
            label.
        """
        return self.name


class TemplateVar(BaseVar):
    """Class to define default variable as a template to ease variable instantiation."""

    def building_informations(self) -> dict:
        """Self's informations to instanciate object with same informations as self.

        Returns
        -------
        dict
            arguments to use when initiating an instance of BaseVar.
        """
        return {
            "name": self.name,
            "unit": self.unit,
            "var_type": self.type,
            "default": self.default,
            "name_format": self.name_format,
            "value_format": self.value_format,
        }

    def in_file_as(self, *args: str | tuple[str, str, list]) -> "ExistingVar":
        """Return an ExistingVar.

        New object has same attributes as self and \
        the property 'aliases' correctly set up using ExistingVar._set_aliases method.

        Parameters
        ----------
        args : str | tuple[str, str, list]
            Name(s) of the variable in the dataset and the corresponding flags.
            Aliases are ranked: first will be the only one used if present in dataset.
            If not second will be checked, and so on..
            Aliases are supposed to be formatted as : (alias, flag_alias, flag_values),
            where alias (str) is the name of the column storing the variable
            in the dataset, flag_alias (str) is the name of the column storing
            the variable's flag in the dataset and flag_values (list) is
            the list of correct values for the flag.
            If there is no flag columns, flag_alias and flag_values can be set to None,
            or the argument can be reduced to the variable column name only.

        Returns
        -------
        ExistingVar
            Variable with correct loading informations.

        Examples
        --------
        To instantiate a variable specifying a flag column to use:
        >>> default_var = TemplateVar("PSAL", "[psu]", float, 10, 9, "%-10s", "%10.3f")
        >>> instanciated_var = default_var.in_file_as(("CTDSAL", "CTDSAL_FLAG_W", [2]))

        To instantiate a variable without flag columns to use:
        >>> default_var = TemplateVar("PSAL", "[psu]", float, 10, 9, "%-10s", "%10.3f")
        >>> instanciated_var = default_var.in_file_as(("CTDSAL",None,None))
        # or equivalently:
        >>> default_var = TemplateVar("PSAL", "[psu]", float, 10, 9, "%-10s", "%10.3f")
        >>> instanciated_var = default_var.in_file_as("CTDSAL")

        To instantiate a variable with multiple possible aliases and flags:
        >>> default_var = TemplateVar("PSAL", "[psu]", float, 10, 9, "%-10s", "%10.3f")
        >>> instanciated_var = default_var.in_file_as(
        >>>     ("CTDSAL1", "CTDSAL1_FLAG_W", [2]),
        >>>     ("CTDSAL2", "CTDSAL2_FLAG_W", [2]),
        >>> )

        To instantiate a variable with multiple possible aliases and some flags:
        >>> default_var = TemplateVar("PSAL", "[psu]", float, 10, 9, "%-10s", "%10.3f")
        >>> instanciated_var = default_var.in_file_as(
        >>>     ("CTDSAL1", "CTDSAL1_FLAG_W", [2]),
        >>>     ("CTDSAL2", None, None),
        >>> )
        # or equivalently:
        To instantiate a variable with multiple possible aliases and some flags:
        >>> default_var = TemplateVar("PSAL", "[psu]", float, 10, 9, "%-10s", "%10.3f")
        >>> instanciated_var = default_var.in_file_as(
        >>>     ("CTDSAL1", "CTDSAL1_FLAG_W", [2]),
        >>>     "CTDSAL2",
        >>> )
        """
        return ExistingVar.from_template(self).set_aliases(*args)

    def not_in_file(self) -> "NotExistingVar":
        """Return a NotExistingVar object with same attributes as self.

        Returns
        -------
        NotExistingVar
            Instanciated variable.
        """
        return NotExistingVar.from_template(self)


class NotExistingVar(BaseVar):
    """Class to represent variables which don't exist in the dataset.

    Parameters
    ----------
    name : str
        'Official' name for the variable : name to use when displaying the variable.
    unit : str
        Variable unit (written using the following format:
        [deg_C] for Celsius degree of [kg] for kilograms).
    var_type : str
        Variable type (str, int, datetime...).
        It will be used to convert the data using df[variable].astype(type)
    default: Any
        Default value to set instead of nan., by default np.nan
    name_format: str
        Format to use to save the data name and unit in a csv of txt file.
        , by default "%-15s"
    value_format: str
        Format to use to save the data value in a csv of txt file., by default "%15s"
    """

    __default_exist_in_dset: bool = False
    __default_remove_if_nan: bool = False
    __default_remove_if_all_nan: bool = False

    def __init__(
        self,
        name: str,
        unit: str,
        var_type: str,
        default: Any = np.nan,
        name_format: str = "%-15s",
        value_format: str = "%15s",
    ):
        """Class to represent variables which don't exist in the dataset.

        Parameters
        ----------
        name : str
            'Official' name for the variable : name to use when displaying the variable.
        unit : str
            Variable unit (written using the following format:
            [deg_C] for Celsius degree of [kg] for kilograms).
        var_type : str
            Variable type (str, int, datetime...).
            It will be used to convert the data using df[variable].astype(type)
        default: Any
            Default value to set instead of nan., by default np.nan
        name_format: str
            Format to use to save the data name and unit in a csv of txt file.
            , by default "%-15s"
        value_format: str
            Format to use to save the data value in a csv/txt file., by default "%15s"
        """
        super().__init__(name, unit, var_type, default, name_format, value_format)
        self.exist_in_dset = self.__default_exist_in_dset
        self._remove_if_nan = self.__default_remove_if_nan
        self._remove_if_all_nan = self.__default_remove_if_all_nan

    @property
    def remove_if_nan(self) -> bool:
        """True if the variable must be removed if NaN.

        Returns
        -------
        bool
            True if the variable must be removed if NaN.
        """
        return self._remove_if_nan

    @property
    def remove_if_all_nan(self) -> bool:
        """Whether the variable must be removed if all same are NaN.

        If True, then the variable must be removed when this variable and
        other 'remove if all nan' variables are NaN.

        Returns
        -------
        bool
            True if the variable must be removed when this variable and
            other 'remove if all nan' variables are NaN.
        """
        return self._remove_if_all_nan

    @classmethod
    def from_template(cls, template: "TemplateVar") -> "NotExistingVar":
        """Instantiate a NotExistingVar from a TemplateVar.

        Parameters
        ----------
        template : TemplateVar
            Template variable to build from.

        Returns
        -------
        NotExistingVar
            NotExistingVar from template.
        """
        return cls(**template.building_informations())

    def set_default(self, default: Any) -> "NotExistingVar":
        """Set the default value for the variable column.

        Parameters
        ----------
        default : Any
            Value to use as default

        Returns
        -------
        NotExistingVar
            Self.
        """
        self.default = default
        return self

    def remove_when_all_nan(self) -> "NotExistingVar":
        """Set self._remove_if_all_nan to True.

        Returns
        -------
        NotExistingVar
            self
        """
        self._remove_if_all_nan = True
        return self

    def remove_when_nan(self) -> "NotExistingVar":
        """Set self._remove_if_nan to True.

        Returns
        -------
        NotExistingVar
            self
        """
        self._remove_if_nan = True
        return self


class ExistingVar(NotExistingVar):
    """Class to represent variables existing in the dataset.

    This class allows to specify flag columns, correction functions...

    Parameters
    ----------
    name : str
        'Official' name for the variable : name to use when displaying the variable.
    unit : str
        Variable unit (written using the following format:
        [deg_C] for Celsius degree of [kg] for kilograms).
    var_type : str
        Variable type (str, int, datetime...).
        It will be used to convert the data using df[variable].astype(type)
    default: Any
        Default value to set instead of nan., by default np.nan
    name_format: str
        Format to use to save the data name and unit in a csv of txt file.
        , by default "%-15s"
    value_format: str
        Format to use to save the data value in a csv of txt file., by default "%15s"
    """

    __default_exist_in_dset: bool = True
    __default_correction: callable = None
    __default_aliases: ClassVar[list[tuple[str, str, list]]] = []

    def __init__(
        self,
        name: str,
        unit: str,
        var_type: str,
        default: Any = np.nan,
        name_format: str = "%-15s",
        value_format: str = "%15s",
    ):
        """Class to represent variables existing in the dataset.

        This class allows to specify flag columns, correction functions...

        Parameters
        ----------
        name : str
            'Official' name for the variable : name to use when displaying the variable.
        unit : str
            Variable unit (written using the following format:
            [deg_C] for Celsius degree of [kg] for kilograms).
        var_type : str
            Variable type (str, int, datetime...).
            It will be used to convert the data using df[variable].astype(type)
        default: Any
            Default value to set instead of nan., by default np.nan
        name_format: str
            Format to use to save the data name and unit in a csv of txt file.
            , by default "%-15s"
        value_format: str
            Format to use to save the data value in a csv/txt file., by default "%15s"
        """
        super().__init__(name, unit, var_type, default, name_format, value_format)
        self.exist_in_dset = self.__default_exist_in_dset
        self.correction = self.__default_correction
        self._aliases = self.__default_aliases.copy()

    @property
    def aliases(self) -> list[tuple[str, str, list]]:
        """Getter for aliases.

        Returns
        -------
        list[tuple[str, str, list]]
            alias, flag column alias (None if not),
            values to keep from flag column (None if not)
        """
        return self._aliases

    @property
    def remove_if_all_nan(self) -> bool:
        """Whether or not to suppress the row when this an other variables are NaN.

        Returns
        -------
        bool
            True if this variable must be included when removing where
            some variables are all nan.
        """
        return self._remove_if_all_nan

    @property
    def remove_if_nan(self) -> bool:
        """Whether or not to suppress the row when the variable is np.nan.

        Returns
        -------
        bool
            True if rows must be removed when this variable is nan.
        """
        return self._remove_if_nan

    @classmethod
    def from_template(cls, template: "TemplateVar") -> "ExistingVar":
        """Instantiate a ExistingVar from a TemplateVar.

        Parameters
        ----------
        template : TemplateVar
            Template variable to build from.

        Returns
        -------
        ExistingVar
            ExistingVar from template.
        """
        return super().from_template(template)

    def set_aliases(self, *args: str | tuple[str, str, list]) -> "ExistingVar":
        """Set aliases for the variable.

        Parameters
        ----------
        args : str | tuple[str, str, list]
            Name(s) of the variable in the dataset and the corresponding flags.
            Aliases are ranked: first alias will be the only one considered if present
            in dataset. If not second will be checked, and so on..
            Aliases are supposed to be formatted as : (alias, flag_alias, flag_values),
            where alias (str) is the name of the column storing the variable
            in the dataset, flag_alias (str) is the name of the column storing
            the variable's flag in the dataset and flag_values (list) is the list
            of correct values for the flag.
            If there is no flag columns, flag_alias and flag_values can be set to None,
            or the argument can be reduced to the variable column name only.

        Returns
        -------
        "ExistingVar"
            Updated version of self

        Raises
        ------
        ValueError
            If one of the arguments length is different than 1 and 3.
        ValueError
            If one of the arguments is not an instance of string or Iterable.
        """
        aliases = []
        for arg in args:
            if isinstance(arg, str):
                alias = arg
                flag_alias = None
                flag_value = None
            elif isinstance(arg, Iterable):
                if len(arg) == 1:
                    alias = arg[0]
                    flag_alias = None
                    flag_value = None
                elif len(arg) == 3:
                    alias = arg[0]
                    flag_alias = arg[1]
                    flag_value = arg[2]
                else:
                    raise ValueError(f"{arg} can't be of length {len(arg)}")
            else:
                raise ValueError(f"{arg} must be str or Iterable")
            aliases.append((alias, flag_alias, flag_value))
        self._aliases = aliases
        return self

    def correct_with(self, function: Callable) -> "ExistingVar":
        """Correction function definition.

        Parameters
        ----------
        function : Callable
            Function to apply to the dataframe row storing this variable's values.

        Returns
        -------
        ExistingVar
            self.

        Raises
        ------
        VariableInstantiationError
            If the given object is not callable.
        """
        if not isinstance(function, Callable):
            raise VariableInstantiationError("Correcting function must be callable.")
        self.correction = function
        self._has_correction = True
        return self


class ParsedVar(BaseVar):
    """Variables parsed from a csv file."""

    def __repr__(self) -> str:
        """Represent the parsed variable as a string.

        Returns
        -------
        str
            name_unit
        """
        return f"{self.name}_{self.unit}"


class FeaturedVar(BaseVar):
    """Variable resulting of an operation between variables.

    Parameters
    ----------
    feature : BaseFeature
        Feature the variable comes from.
    """

    is_feature = True

    def __init__(self, feature: "BaseFeature"):
        super().__init__(
            feature.variable.name,
            feature.variable.unit,
            feature.variable.type,
            feature.variable.default,
            feature.variable.name_format,
            feature.variable.value_format,
        )
        self._feature = feature
        self.required_vars = feature.required_variables
