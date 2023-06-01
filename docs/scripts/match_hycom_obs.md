# Match Simulation Points to Observations

Simulation Data (from HYCOM model) is provided on a 3D grid. The observation datapoints can be anywhere within this grid. Therefore, to compare observations and simulations, one must match observation datapoints to their "corresponding" simulation point.

## Defining Closest Point Value

1. Find the Closest point on a the 2D grid:

    Since HYCOM output file are provided with a "Grid File", a file containing only latitude and longitude coordinates of all simulated points. Using this values, it is possible to find the closest simulated point to a given observed point (only considering latitude and longitude). This is done using [scikit-learn's NearestNeighbor Algorithm](https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.NearestNeighbors.html) with the following parameters:

     - `n_neighbors=1`
