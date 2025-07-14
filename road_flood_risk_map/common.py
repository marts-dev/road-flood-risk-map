"""The common module contains common functions and classes used by the other modules.
"""

import numpy as np

def compute_d8_direction(dem):
    """Compute D8 flow direction from a DEM."""
    # Placeholder for D8 direction computation logic
    # This should return a numpy array of the same shape as dem
    # with values indicating the flow direction.
    direction_code = {
        32:(-1, -1),  # 0: North-West
        64:(0, -1),   # 1: North
        128:(1, -1),   # 2: North-East
        1:(1, 0),    # 3: East
        2:(1, 1),    # 4: South-East
        4:(0, 1),    # 5: South
        8:(-1, 1),   # 6: South-West
        16:(-1, 0)    # 7: West
    }
    d8_direction = np.zeros_like(dem, dtype=np.int32)
    rows, cols = dem.shape
    for i in range(0, rows):
        for j in range(0, cols):
            if dem[i, j] == -9999:  # Assuming -9999 is the nodata value
                d8_direction[i, j] = -1
            else:
                # Compute the direction based on the surrounding cells
                maximum_drop = -np.inf
                elev = dem[i, j]
                direction = -1
                for k, (dj, di) in direction_code.items():
                    ni, nj = i + di, j + dj
                    if 0 <= ni < rows and 0 <= nj < cols:
                        #maximum_drop = change_in_z-value / distance * 100
                        change_in_z = elev - dem[ni, nj]
                        distance = np.sqrt(di**2 + dj**2)
                        drop = (change_in_z / distance * 100) if distance != 0 else 0
                        if drop > maximum_drop:
                            maximum_drop = drop
                            direction = k
                d8_direction[i, j] = direction
    return d8_direction

def fill_depression(dem):
    """Fill depressions in a DEM using D8 flow direction."""
    # Placeholder for depression filling logic
    # This should modify the dem in place or return a new filled DEM.
    # Ref: https://arxiv.org/pdf/1511.04463
    import heapq
    import numpy as np
    import queue
    rows, cols = dem.shape
    open_pq = []
    pits = queue.Queue()
    closed_set = np.zeros((rows, cols), dtype=bool)

    # Initialize the priority queue with border cells
    for i in range(rows):
        heapq.heappush(open_pq, (dem[i, 0], (i, 0)))
        heapq.heappush(open_pq, (dem[i, cols-1], (i, cols-1)))
        closed_set[i, 0] = True
        closed_set[i, cols-1] = True

    for j in range(1, cols - 1):
        heapq.heappush(open_pq, (dem[0, j], (0, j)))
        heapq.heappush(open_pq, (dem[rows-1, j], (rows-1, j)))
        closed_set[0, j] = True
        closed_set[rows-1, j] = True

    while not open_pq.empty() or not pits.empty():
        current = None
        if not pits.empty():
            current = pits.get()
        else:
            current = heapq.heappop(open_pq)

        # Process neighbors of current cell
        

    return dem