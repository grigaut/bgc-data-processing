"""Loadings tools for Argo measurements files"""


import os

import netCDF4 as nc


class NetCDFStorer:
    def __init__(
        self,
        filepath: str,
        mode: str = "r",
        **kwargs,
    ) -> None:
        """Wrapper class for netCDF4.Dataset to store additionnal informations.

        Parameters
        ----------
        filepath : str
            Path to the file
        mode : str, optional
            Reading mode for netCDF4.Dataset., by default "r"
        **kwargs : dict
            Additional loading parametrs.
            The keywords arguments are passed to 'netCDF4.Dataset'
        """
        self.filepath = filepath
        self.open_mode = mode
        self.open_kwargs = kwargs
        self.name = filepath.split("/")[-1]
        self.id = self.__parse_file()
        self.__content = None

    def __parse_file(
        self,
    ) -> str:
        """Parses filename to find station's ID.
        Works pour filenames following one of these patterns : 'GL_PR_PF_1901338.nc' or '5903592_prof.nc'.

        Returns
        -------
        str
            Station's ID
        """
        if self.name[0:2] == "GL":
            return self.name[9:16]
        else:
            return self.name[0:7]

    def __open(
        self,
    ) -> None:
        """Opens a .nc file using netCDF4.Dataset."""

        self.__content = nc.Dataset(
            self.filepath,
            self.open_mode,
            **self.open_kwargs,
        )

    def __eq__(
        self,
        object,
    ) -> bool:
        """Tests equality

        Parameters
        ----------
        object :
            Object to test the equality with

        Returns
        -------
        bool
            True if the object has the same id as self

        Notes
        -----
        Will return True if the object has the same id as self or
        if the object is a string which value matches self's id.
        """
        if isinstance(object, str):
            return self.name == object
        elif isinstance(object, NetCDFStorer):
            return self.name == object.name
        else:
            return False

    def get_id(self) -> str:
        """Returns  self.id

        Returns
        -------
        str
            nc file's id.
        """
        return self.id

    def get_name(self) -> str:
        """Returns self.filename

        Returns
        -------
        str
            Filename
        """
        return self.name

    def get_content(
        self,
    ) -> nc.Dataset:
        """Returns self.__content

        Returns
        -------
        nc.Dataset
            Content of the nc file
        """
        if self.__content is None:
            self.__open()
        return self.__content


def load_netcdf(
    filepath: str,
) -> NetCDFStorer:
    """Loads a .nc file

    Parameters
    ----------
    filepath : str
        Path to the file.

    Returns
    -------
    NetCDFStorer
        Loaded object
    """

    ncfile = NetCDFStorer(filepath, "r")
    return ncfile


def load_files_from_dir(
    path: str,
) -> list[NetCDFStorer]:
    """Loads .nc file(s) from a file or a directory.

    Parameters
    ----------
    path : str
        Path to the file or directory.

    Returns
    -------
    list[NetCDFStorer]
        List of all loaded files.

    Raises
    ------
    NotADirectoryError
        If the filepath doesn't refer to an existing file or directory.
    """
    loaded = []
    if os.path.isdir(path):
        for file in os.listdir(path):
            filepath = path + "/" + file
            loaded.append(
                load_netcdf(
                    filepath=filepath,
                )
            )
    elif os.path.isfile(path):
        loaded.append(
            load_netcdf(
                filepath=path,
            )
        )
    else:
        raise NotADirectoryError(f"{path} is not a directory")
    return loaded
