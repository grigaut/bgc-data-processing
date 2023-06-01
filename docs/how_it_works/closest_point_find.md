# Match Simulation Points to Observations

Simulation Data (from HYCOM model) is provided on a 3D grid. The observation datapoints can be anywhere within this grid. Therefore, to compare observations and simulations, one must match observation datapoints to their "corresponding" simulation point.

## Defining Closest Point Value

1. Finding the Closest point on a the 2D grid:

    Since HYCOM output file are provided with a "Grid File", a file containing only latitude and longitude coordinates of all simulated points. Using this values, it is possible to find the closest simulated point to a given observed point (only considering latitude and longitude). This is done using [scikit-learn's NearestNeighbor Algorithm](https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.NearestNeighbors.html) with the following parameters:

     - `n_neighbors=1` -> Only the closest point is required
     - `metric = "haversine"` -> [Great-circle distance between two points on a sphere](https://en.wikipedia.org/wiki/Haversine_formula)


2. Loading all simulated point at this location for the given date
3. Finding the right value in depth:

    Instead of finding the closest depth value within the avalaible levels, the simulated point values are interpolated from water profile.

Therefore, in the end, the "closest point" is the point which latitude and longitude are the closest to the observation (relative to the Haversine metric) and values have been interpolated to match the observation's depth.
