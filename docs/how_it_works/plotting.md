# Plotting

All plotting object derive from the same class: [BasePlot]({{fix_url("../reference/tracers/#bgc_data_processing.tracers.BasePlot")}}). Therefore, these classes all share the same public methods:

- [show]({{fix_url("../reference/tracers/#bgc_data_processing.tracers.BasePlot.show")}}): Show the figure in a new [Figure](https://matplotlib.org/stable/api/figure_api.html#matplotlib.figure.Figure).
- [save]({{fix_url("../reference/tracers/#bgc_data_processing.tracers.BasePlot.save")}}): Save the figure in a file (file suffix must be `.png`)
- [plot_to_axes]({{fix_url("../reference/tracers/#bgc_data_processing.tracers.BasePlot.plot_to_axes")}}): Add the figure to an already existing [Axes](https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.html#matplotlib.axes.Axes) instance.

## Overview:

All the following plotting objects are defined in [tracers.py]({{fix_url("../reference/tracers")}}).

### Meshplot

Plot Data Density on a map.

![MeshPlot]({{fix_url("assets/plots/mesh.png")}}){width=750px}

### EvolutionProfile

Plot the Data Density profile over the time.

![EvolutionProfile]({{fix_url("assets/plots/profile.png")}}){width=750px}

### TemperatureSalinityDiagram

Plot the Temperature-Salinity Diagram of the given data.

![TemperatureSalinityDiagram]({{fix_url("assets/plots/TS_diagram.png")}}){width=750px}

### VariableBoxPlot

Plot the Box plots of a given variable for different water masses.

![variableBoxPlot]({{fix_url("assets/plots/boxplot.png")}}){width=750px}

### VariableHistogram

Plot the histograms of a given variable for different water masses.

![VariableHistogram]({{fix_url("assets/plots/histogram.png")}}){width=750px}

### WaterMassVariableComparison

Plot the values of variable vs pressure for all given water_masses.

![WaterMassVariableComparison]({{fix_url("assets/plots/wm_comparison.png")}}){width=750px}
