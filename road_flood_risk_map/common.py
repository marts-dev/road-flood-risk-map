"""The common module contains common functions and classes used by the other modules."""

import numpy as np


def compute_d8_direction(dem, nodata_value=np.nan):
    """Compute D8 flow direction from a DEM."""
    # Placeholder for D8 direction computation logic
    # This should return a numpy array of the same shape as dem
    # with values indicating the flow direction.
    direction_code = {
        32: (-1, -1),  # 0: North-West
        64: (-1, 0),  # 1: North
        128: (-1, 1),  # 2: North-East
        1: (0, 1),  # 3: East
        2: (1, 1),  # 4: South-East
        4: (0, 1),  # 5: South
        8: (1, -1),  # 6: South-West
        16: (0, -1),  # 7: West
    }
    d8_direction = np.zeros_like(dem, dtype=np.int32)
    rows, cols = dem.shape
    for i in range(0, rows):
        for j in range(0, cols):
            if dem[i, j] == nodata_value:  # Assuming -9999 is the nodata value
                d8_direction[i, j] = nodata_value
            else:
                # Compute the direction based on the surrounding cells
                maximum_drop = -np.inf
                elev = dem[i, j]
                direction = -1
                for k, (di, dj) in direction_code.items():
                    ni, nj = i + di, j + dj
                    if 0 <= ni < rows and 0 <= nj < cols:
                        # maximum_drop = change_in_z-value / distance * 100
                        change_in_z = elev - dem[ni, nj]
                        distance = np.sqrt(di**2 + dj**2)
                        drop = (change_in_z / distance * 100) if distance != 0 else 0
                        if drop > maximum_drop:
                            maximum_drop = drop
                            direction = k
                d8_direction[i, j] = direction
    return d8_direction


def fill_depressions(dem):
    """
    Fill depressions in a DEM using a simple algorithm.
    """
    import heapq
    import numpy as np
    import queue

    filled_dem = dem.copy()
    rows, cols = dem.shape
    open_pq = []
    pits = queue.Queue()
    closed_set = np.zeros((rows, cols), dtype=bool)

    neighbors = [
        (-1, 0),  # North
        (1, 0),  # South
        (0, -1),  # West
        (0, 1),  # East
        (-1, -1),  # Northwest
        (-1, 1),  # Northeast
        (1, -1),  # Southwest
        (1, 1),  # Southeast
    ]

    # Initialize the priority queue with border cells
    for i in range(rows):
        heapq.heappush(open_pq, (dem[i, 0], (i, 0)))
        heapq.heappush(open_pq, (dem[i, cols - 1], (i, cols - 1)))
        closed_set[i, 0] = True
        closed_set[i, cols - 1] = True

    for j in range(1, cols - 1):
        heapq.heappush(open_pq, (dem[0, j], (0, j)))
        heapq.heappush(open_pq, (dem[rows - 1, j], (rows - 1, j)))
        closed_set[0, j] = True
        closed_set[rows - 1, j] = True

    while open_pq or not pits.empty():
        current = None
        if not pits.empty():
            current = pits.get()
        else:
            current = heapq.heappop(open_pq)

        # Process neighbors of current cell
        for dx, dy in neighbors:
            nx, ny = current[1][0] + dx, current[1][1] + dy
            if 0 <= nx < rows and 0 <= ny < cols and not closed_set[nx, ny]:
                neighbor_value = dem[nx, ny]

                closed_set[nx, ny] = True
                if neighbor_value <= current[0]:
                    # If neighbor is lower, add to pits
                    filled_dem[nx, ny] = current[0]
                    pits.put((neighbor_value, (nx, ny)))
                else:
                    # Otherwise, add to open set
                    heapq.heappush(open_pq, (neighbor_value, (nx, ny)))

    return filled_dem


def fill_depression_epsilon(dem, nodata_value=-9999):
    """
    Fill depressions in a DEM using an epsilon-based approach.
    """
    import heapq
    import numpy as np
    import queue

    filled_dem = dem.copy()
    rows, cols = dem.shape
    open_pq = []
    pits = queue.Queue()
    closed_set = np.zeros((rows, cols), dtype=bool)

    neighbors = [
        (-1, 0),  # North
        (1, 0),  # South
        (0, -1),  # West
        (0, 1),  # East
        (-1, -1),  # Northwest
        (-1, 1),  # Northeast
        (1, -1),  # Southwest
        (1, 1),  # Southeast
    ]

    # Initialize the priority queue with border cells
    for i in range(rows):
        heapq.heappush(open_pq, (dem[i, 0], (i, 0)))
        heapq.heappush(open_pq, (dem[i, cols - 1], (i, cols - 1)))
        closed_set[i, 0] = True
        closed_set[i, cols - 1] = True

    for j in range(1, cols - 1):
        heapq.heappush(open_pq, (dem[0, j], (0, j)))
        heapq.heappush(open_pq, (dem[rows - 1, j], (rows - 1, j)))
        closed_set[0, j] = True
        closed_set[rows - 1, j] = True

    pit_top = None
    false_pit_cells = 0
    while open_pq or not pits.empty():
        current = None

        if open_pq and (open_pq[0][0] == pit_top):
            current = heapq.heappop(open_pq)
            pit_top = None
        elif not pits.empty():
            current = pits.get()
            if pit_top is None:
                pit_top = dem[current[1][0], current[1][1]]
        else:
            current = heapq.heappop(open_pq)
            pit_top = None

        # Process neighbors of current cell
        for dx, dy in neighbors:
            nx, ny = current[1][0] + dx, current[1][1] + dy
            if 0 <= nx < rows and 0 <= ny < cols and not closed_set[nx, ny]:
                neighbor_value = dem[nx, ny]

                closed_set[nx, ny] = True
                if neighbor_value == nodata_value or np.isnan(neighbor_value):
                    pits.put((neighbor_value, (nx, ny)))
                elif neighbor_value <= np.nextafter(current[0], np.float64("inf")):
                    next_after_value = np.nextafter(current[0], np.float64("inf"))
                    if pit_top is not None and (
                        pit_top < neighbor_value and next_after_value >= neighbor_value
                    ):
                        false_pit_cells += 1
                    filled_dem[nx, ny] = next_after_value
                    pits.put((neighbor_value, (nx, ny)))
                else:
                    # Otherwise, add to open set
                    heapq.heappush(open_pq, (neighbor_value, (nx, ny)))

    return filled_dem


def fill_depressions_flow_dirs(dem):
    """
    Fill depressions in a DEM using a simple algorithm.
    """
    import heapq
    import numpy as np
    import queue

    def get_opposite_direction(x, y):
        """Get the opposite direction for a given D8 direction."""
        return [-x, -y]

    rows, cols = dem.shape
    open_pq = []
    closed_set = np.zeros((rows, cols), dtype=bool)
    flow_dirs = np.zeros_like(dem, dtype=np.int32)

    direction_code = {
        (-1, 0): 64,  # 1: North
        (0, 1): 1,  # 3: East
        (0, 1): 4,  # 5: South
        (0, -1): 16,  # 7: West
        (-1, -1): 32,  # 0: North-West
        (-1, 1): 128,  # 2: North-East
        (1, 1): 2,  # 4: South-East
        (1, -1): 8,  # 6: South-West
    }

    # Initialize the priority queue with border cells
    for i in range(rows):
        heapq.heappush(open_pq, (dem[i, 0], (i, 0)))
        heapq.heappush(open_pq, (dem[i, cols - 1], (i, cols - 1)))
        closed_set[i, 0] = True
        if np.isnan(dem[i, 0]):
            flow_dirs[i, 0] = None
        else:
            flow_dirs[i, 0] = 1
        closed_set[i, cols - 1] = True
        if np.isnan(dem[i, cols - 1]):
            flow_dirs[i, cols - 1] = None
        else:
            flow_dirs[i, cols - 1] = 16

    for j in range(1, cols - 1):
        heapq.heappush(open_pq, (dem[0, j], (0, j)))
        heapq.heappush(open_pq, (dem[rows - 1, j], (rows - 1, j)))
        closed_set[0, j] = True
        if np.isnan(dem[0, j]):
            flow_dirs[0, j] = None
        else:
            flow_dirs[0, j] = 64
        closed_set[rows - 1, j] = True
        if np.isnan(dem[rows - 1, j]):
            flow_dirs[rows - 1, j] = None
        else:
            flow_dirs[rows - 1, j] = 4

    while open_pq:
        current = heapq.heappop(open_pq)

        # Process neighbors of current cell
        for (dx, dy), direction in direction_code.items():
            nx, ny = current[1][0] + dx, current[1][1] + dy
            if 0 <= nx < rows and 0 <= ny < cols and not closed_set[nx, ny]:
                neighbor_value = dem[nx, ny]
                if np.isnan(neighbor_value):
                    flow_dirs[nx, ny] = None
                else:
                    ox, oy = get_opposite_direction(nx, ny)
                    flow_dirs[nx, ny] = direction[(ox, oy)]
                closed_set[nx, ny] = True
                heapq.heappush(open_pq, (neighbor_value, (nx, ny)))

    return flow_dirs


def fix_raster_metadata(file_name: str, output_name: str):
    """
    Converts the compress method string of the Raster file to uppercase as supported by WhiteBoxTools.

    Args:
        file_name (str): Raster file to modify
        output_name (str): Output raster file name without extension

    Returns:
        path (str): Full path of the output raster file
    """
    import rasterio
    from rasterio.transform import Affine
    import os

    with rasterio.open(file_name) as src:
        profile = src.profile.copy()
        profile.update(compress=profile["compress"].upper())
        profile.update(nodata=-9999)
        bounds = src.bounds
        # Fix bounds
        shift = 0
        if bounds.left < -180:
            shift = 360
        elif bounds.right > 180:
            shift = -360
        if shift != 0:
            new_transform = Affine.translation(shift, 0) * src.transform
            profile.update(transform=new_transform)
            print(f"Fixed bounds by shifting {shift} degrees.")
        with rasterio.open(f"{output_name}.tif", "w", **profile) as dst:
            dst.write(src.read())
    os.remove(file_name)
    return f"{os.path.join(os.getcwd(),output_name)}.tif"
