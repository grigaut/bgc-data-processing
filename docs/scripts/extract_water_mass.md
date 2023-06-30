# Water Mass Extraction

`make run-extract-water-mass`

## Summary

This script extracts data from a given watermass and saves it into a given folder.

## Configuration
The configuration file for this script is `config/extract_water_mass.toml` (based on [`config/default/extract_water_mass.toml`]({{repo_blob}}/config/default/extract_water_mass.toml)). All the parameters and their functionality are listed below:

### **Input/Output**
??? question "LOADING_DIR"
    Directory from which to load data.

    **default**: `"bgc_data"`

    Expected type: `str`

??? question "SAVING_DIR"
    Directory in which to save extracted data.

    **default**: `"extracted_watermass"`

    Expected type: `str`
### **Data Selection**
??? question "WATER_MASS_ACRONYM"
    Acronym of the water mass to extract. The water mass acronyms are the acronyms defined in config/water_masses.toml (based on [config/default/water_masses.toml]({{repo_blob}}/config/default/water_masses.toml)). The acronym is the value defined under the `ACRONYM` parameter.

    **default**: `ALL`

    Expected type: `str`

??? question "DATE_MIN"
    Beginning of the data to load (included).

    **default**: `"20070101"`

    Expected type: `str` (respecting the `YYYYMMDD` format)

??? question "DATE_MAX"
    End of the data to load (included).

    **default**: `"20071231"`

    Expected type: `str` (respecting the `YYYYMMDD` format)

??? question "LATITUDE_MIN"
    Minimum latitude boundary for the loaded data (included).

    **default**: `60`

    Expected type: `int`or `float`

??? question "LATITUDE_MAX"
    Maximum latitude boundary for the loaded data (included).

    **default**: `80`

    Expected type: `int`or `float`

??? question "LONGITUDE_MIN"
    Minimum longitude boundary for the loaded data (included).

    **default**: `-50`

    Expected type: `int`or `float`

??? question "LONGITUDE_MAX"
    Maximum longitude boundary for the loaded data (included).    Only used if `FROM_POLYGON` is set to `false`.

    **default**: `50`

    Expected type: `int`or `float`

??? question "PRIORITY"
    Providers priority list to use when removing duplicates.

    **default**: `["GLODAP_2022", "CMEMS", "ARGO", "NMDC", "CLIVAR", "IMR", "ICES"]`

    Expected type: `list[str]`
### **Others**
??? question "VERBOSE"
    Verbose value, the higher, the more informations. If set to 0 or below: no information displayed. If set to 1: minimal informations displayed. If set to 2: very complete informations displayed. If set to 3 or higher: exhaustive informations displayed.

    **default**: `2`

    Expected type: `int`
## Script Output
When executed, this script will create a file in the `SAVING_DIR` folder with the extracted data.

This is an example of what this data could look like:

![Water Mass Extraction output example]({{fix_url("assets/plots/saved_data.png")}}){width=750px}

Source code: [:octicons-file-code-16:]({{repo_blob}}/scripts/extract_water_mass.py)
