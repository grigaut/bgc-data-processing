"""Variable related objects."""

from abc import ABC
from typing import Any, Callable, Iterable, Iterator, Self

import numpy as np
from _collections_abc import dict_keys

from bgc_data_processing.exceptions import VariableInstantiationError


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

        self.name = name
        self.unit = unit
        self.type = var_type
        self.default = default
        self.name_format = name_format
        self.value_format = value_format

    def __str__(self) -> str:
        return f"{self.name} - {self.unit} ({self.type})"

    def __repr__(self) -> str:
        txt = f"{self.name}_{self.unit}_{self.type}"
        return txt

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, BaseVar):
            return repr(self) == repr(__o)
        else:
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

    def _building_informations(self) -> dict:
        """Self's informations to instanciate object with same informations as self.

        Returns
        -------
        dict
            arguments to use when initiating an instance of BaseVar.
        """
        informations = dict(
            name=self.name,
            unit=self.unit,
            var_type=self.type,
            default=self.default,
            name_format=self.name_format,
            value_format=self.value_format,
        )
        return informations

    def in_file_as(self, *args: str | tuple[str, str, list]) -> "ExistingVar":
        """Returns an ExistingVar object with same attributes as self and \
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
        """Returns a NotExistingVar object with same attributes as self.

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
        """True if the variable must be removed when this variable and \
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
        """Instantiates a NotExistingVar from a TemplateVar.

        Parameters
        ----------
        template : TemplateVar
            Template variable to build from.

        Returns
        -------
        NotExistingVar
            NotExistingVar from template.
        """
        var = cls(**template._building_informations())
        return var

    def set_default(self, default: Any) -> Self:
        """Set the default value for the variable column.

        Parameters
        ----------
        default : Any
            Value to use as default

        Returns
        -------
        Self
            Self.
        """
        self._default = default
        return self

    def remove_when_all_nan(self) -> Self:
        """Sets self._remove_if_all_nan to True.

        Returns
        -------
        Self
            self
        """
        self._remove_if_all_nan = True
        return self

    def remove_when_nan(self) -> Self:
        """Sets self._remove_if_nan to True.

        Returns
        -------
        Self
            self
        """
        self._remove_if_nan = True
        return self


class ExistingVar(NotExistingVar):
    """Class to represent variables existing in the dataset, \
    to be able to specify flag columns, correction functions...

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
    __default_aliases: list = []

    def __init__(
        self,
        name: str,
        unit: str,
        var_type: str,
        default: Any = np.nan,
        name_format: str = "%-15s",
        value_format: str = "%15s",
    ):
        super().__init__(name, unit, var_type, default, name_format, value_format)
        self.exist_in_dset = self.__default_exist_in_dset
        self._correction = self.__default_correction
        self._aliases = self.__default_aliases

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
        """Get the boolean indicating whether or not to suppress the row when multiple \
        variables (this one included if True) are np.nan.

        Returns
        -------
        bool
            True if this variable must be included when removing where
            some variables are all nan.
        """
        return self._remove_if_all_nan

    @property
    def remove_if_nan(self) -> bool:
        """Get the boolean indicating whether or not to suppress the row when \
        the variable is np.nan.

        Returns
        -------
        bool
            True if rows must be removed when this variable is nan.
        """
        return self._remove_if_nan

    @classmethod
    def from_template(cls, template: "TemplateVar") -> "ExistingVar":
        """Instantiates a ExistingVar from a TemplateVar.

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

    def set_aliases(self, *args: str | tuple[str, str, list]) -> Self:
        """Sets aliases for the variable.

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
        Self
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

    def correct_with(self, function: Callable) -> Self:
        """Correction function definition.

        Parameters
        ----------
        function : Callable
            Function to apply to the dataframe row storing this variable's values.

        Returns
        -------
        Self
            self.

        Raises
        ------
        VariableInstantiationError
            If the given object is not callable.
        """
        if not isinstance(function, Callable):
            raise VariableInstantiationError("Correcting function must be callable.")
        self._correction = function
        self._has_correction = True
        return self


class ParsedVar(BaseVar):
    """Variables parsed from a csv file."""

    def __repr__(self) -> str:
        txt = f"{self.name}_{self.unit}"
        return txt


class VariablesStorer:
    """General storer for Var object to represent the set of both variables present \
    in the file and variables to take in consideration \
    (therefore to add even if empty) when loading the data.

    Parameters
    ----------
    expocode : ExistingVar | NotExistingVar
        Expocode related variable.
    date : ExistingVar | NotExistingVar
        Date related variable.
    year : ExistingVar | NotExistingVar
        Year related variable.
    month : ExistingVar | NotExistingVar
        Month related variable.
    day : ExistingVar | NotExistingVar
        Day related variable.
    latitude : ExistingVar | NotExistingVar
        Latitude related variable.
    longitude : ExistingVar | NotExistingVar
        Longitude related variable.
    depth : ExistingVar | NotExistingVar
        Depth related variable.
    provider : ExistingVar | NotExistingVar, optional
        Provider related variable. Can be set to None to be ignored., by default None
    hour : ExistingVar | NotExistingVar, optional
        Hour related variable. Can be set to None to be ignored., by default None
    *args: list
        Var objects to represent the variables stored by the object.
        It is better if these Var object have been instanciated
        using .not_here or .here_as methods.
    *kwargs: dict
        Var objects to represent the variables stored by the object.
        It is better if these Var object have been instanciated
        using .not_here or .here_as methods. The parameter name has no importance.

    Raises
    ------
    ValueError:
        If multiple var object have the same name.
    """

    def __init__(
        self,
        expocode: ExistingVar | NotExistingVar,
        date: ExistingVar | NotExistingVar,
        year: ExistingVar | NotExistingVar,
        month: ExistingVar | NotExistingVar,
        day: ExistingVar | NotExistingVar,
        latitude: ExistingVar | NotExistingVar,
        longitude: ExistingVar | NotExistingVar,
        depth: ExistingVar | NotExistingVar,
        hour: ExistingVar | NotExistingVar = None,
        provider: ExistingVar | NotExistingVar = None,
        *args: ExistingVar | NotExistingVar,
        **kwargs: ExistingVar | NotExistingVar,
    ) -> None:
        if len(args) != len(set(var.name for var in args)):
            raise ValueError(
                "To set multiple alias for the same variable, "
                "use Var.in_file_as([alias1, alias2])"
            )
        mandatory_variables = []
        if provider is None:
            self.has_provider = False
            self.provider_var_name = None
        else:
            self.has_provider = True
            self.provider_var_name = provider.name
            mandatory_variables.append(provider)
        self.expocode_var_name = expocode.name
        mandatory_variables.append(expocode)
        self.date_var_name = date.name
        mandatory_variables.append(date)
        self.year_var_name = year.name
        mandatory_variables.append(year)
        self.month_var_name = month.name
        mandatory_variables.append(month)
        self.day_var_name = day.name
        mandatory_variables.append(day)
        if hour is None:
            self.has_hour = False
            self.hour_var_name = None
        else:
            self.has_hour = True
            self.hour_var_name = hour.name
            mandatory_variables.append(hour)
        self.latitude_var_name = latitude.name
        mandatory_variables.append(latitude)
        self.longitude_var_name = longitude.name
        mandatory_variables.append(longitude)
        self.depth_var_name = depth.name
        mandatory_variables.append(depth)
        self._elements = mandatory_variables + list(args) + list(kwargs.values())
        self._save = mandatory_variables + list(args) + list(kwargs.values())
        self._in_dset = [var for var in self._elements if var.exist_in_dset]
        self._not_in_dset = [var for var in self._elements if not var.exist_in_dset]

    def __getitem__(self, __k: str) -> ExistingVar | NotExistingVar:
        return self.get(__k)

    def __iter__(self) -> Iterator[ExistingVar | NotExistingVar]:
        return iter(self._elements)

    def __str__(self) -> str:
        txt = ""
        for var in self._elements:
            if var.exist_in_dset is None:
                here_txt = "not attributed"
            elif var.exist_in_dset:
                here_txt = var.aliases
            else:
                here_txt = "not in file"
            txt += str(var) + f": {here_txt}\n"
        return txt

    def __len__(self) -> int:
        return len(self._elements)

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, VariablesStorer):
            if len(self) != len(__o):
                return False
            elif set(self._mapper_by_name.keys()) != set(__o._mapper_by_name.keys()):
                return False
            else:
                repr_eq = [
                    repr(self[key]) == repr(__o[key])
                    for key in self._mapper_by_name.keys()
                ]
                return np.all(repr_eq)
        else:
            return False

    def get(self, var_name: str) -> ExistingVar | NotExistingVar:
        """Return the variable which name corresponds to var_name.

        Parameters
        ----------
        var_name : str
            Name of the variable to get.

        Returns
        -------
        ExistingVar | NotExistingVar
            Variable with corresponding name in self._elements.

        Raises
        ------
        KeyError
            If var_name doesn't correspond to any name.
        """
        if self.has_name(var_name=var_name):
            return self._mapper_by_name[var_name]
        else:
            valid_keys = self._mapper_by_name.keys()
            error_msg = (
                f"{var_name} is not a valid variable name."
                f"Valid names are: {list(valid_keys)}"
            )
            raise KeyError(error_msg)

    def add_var(self, var: ExistingVar | NotExistingVar) -> None:
        """Adds a new variable to self._elements.

        Parameters
        ----------
        var : Var
            Variable to add
        """
        if var.name in self.keys():
            raise ValueError("A variable already exists with his name")
        self._elements.append(var)

    def has_name(self, var_name: str) -> bool:
        """Checks if a variable name is the nam eof one of the variables.

        Parameters
        ----------
        var_name : str
            Name to test.

        Returns
        -------
        bool
            True if the name is in self.keys(), False otherwise.
        """
        return var_name in self.keys()

    def keys(self) -> dict_keys:
        """Keys to use when calling self[key].

        Returns
        -------
        dict_keys
            View of self._mapper_by_name keys.
        """
        return self._mapper_by_name.keys()

    def set_saving_order(self, var_names: list[str] = []) -> None:
        """Set the saving order for the variables.

        Parameters
        ----------
        var_names : list[str], optional
            List of variable names => saving variables sorted., by default []

        Raises
        ------
        ValueError
            If a variable name is not one of the variables'.
        """
        if not var_names:
            return
        new_save = [self.get(name) for name in var_names]
        self._save = new_save

    @property
    def labels(self) -> dict[str, str]:
        """Returns a dicitonnary mapping variable names to variables labels.

        Returns
        -------
        dict[str, str]
            name : label
        """
        return {var.name: var.label for var in self._elements}

    @property
    def _mapper_by_name(self) -> dict[str, ExistingVar | NotExistingVar]:
        """Mapper between variables names and variables Var objects (for __getitem__).

        Returns
        -------
        dict[str, Var]
            Mapping between names (str) and variables (Var)
        """
        return {var.name: var for var in self._elements}

    @property
    def unit_mapping(self) -> dict[str, str]:
        """Mapper between variables names and variables units. \
        Mostly used to create unit row.

        Returns
        -------
        dict[str, str]
            Mapping between names (str) and units (str).
        """
        return {var.name: var.unit for var in self._elements}

    @property
    def save_labels(self) -> list[str | tuple[str]]:
        """Sorting order to use when saving data.

        Returns
        -------
        list[str | tuple[str]]
            List of columns keys to pass as df[self.save_sort] to sort data.
        """
        return [var.label for var in self._save]

    @property
    def name_save_format(self) -> str:
        """String line to use as formatting for name and unit rows.

        Returns
        -------
        str
            Format string

        Examples
        --------
        >>> var_year = Var("YEAR", "[]", int, 0, 0,"%-4s", "%4d")
        >>> var_provider = Var("PROVIDER", "[]", str, 1, 1, "%-15s", "%15s")
        >>> storer = VariablesStorer(var_year, var_provider)
        >>> print(storer.name_save_format)
        "%-4s %-15s"
        >>> storer.name_save_format % tuple(storer.save_labels)
        "YEAR PROVIDER "
        """
        format_string = " ".join([var.name_format for var in self._save])
        return format_string

    @property
    def value_save_format(self) -> str:
        """String line to use as formatting for value rows.

        Returns
        -------
        str
            Format string"
        """
        format_string = " ".join([var.value_format for var in self._save])
        return format_string

    @property
    def in_dset(self) -> list[ExistingVar]:
        """List of Var object supposedly present in the dataset.

        Returns
        -------
        list[Var]
            Var objects in the dataset.
        """
        return self._in_dset

    @property
    def corrections(self) -> dict[str, Callable]:
        """Mapping between variables keys and correcting functions.

        Returns
        -------
        dict[str, Callable]
            Mapping.
        """
        return {
            var.label: var._correction
            for var in self._in_dset
            if var._correction is not None
        }

    @property
    def to_remove_if_all_nan(self) -> list[str]:
        """Returns the list of keys to inspect when removing rows where \
        all variables are np.nan.

        Returns
        -------
        list[str]
            List of keys to use.
        """
        return [var.label for var in self._elements if var.remove_if_all_nan]

    @property
    def to_remove_if_any_nan(self) -> list[str]:
        """Returns the list of keys to inspect when removing rows where \
        any variable is np.nan.

        Returns
        -------
        list[str]
            List of keys to use.
        """
        return [var.label for var in self._elements if var.remove_if_nan]
