# Mapper

Mapping tool for measurement campaigns.

## Description

These tools aims at mapping measures campaigns rajectories and to provide the measurements into a profile graph.

## Configuration

In order to modify the filepaths for both input and output directories, one only has to modify `FILIN` (depth level input file path), `DIRIN_ARGO` (Argo measures folder), `dirout` (output directory path) and `DEPTH_MAX` (Maximal depth to consider) variables in [config.py](../../reference/mapper/config/).
However, it is important to keep in mind that the input directory is expected to have the following architecture :
```
DIRIN_ARGO
    file1.nc    # netcdf file
    file2.nc    # netcdf file
    ...
...
```
