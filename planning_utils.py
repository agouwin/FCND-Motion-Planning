from enum import Enum
from queue import PriorityQueue
import numpy as np


def create_grid(data, drone_altitude, safety_distance):
    """
    Returns a grid representation of a 2D configuration space
    based on given obstacle data, drone altitude and safety distance
    arguments.
    """

    # minimum and maximum north coordinates
    north_min = np.floor(np.min(data[:, 0] - data[:, 3]))
    north_max = np.ceil(np.max(data[:, 0] + data[:, 3]))

    # minimum and maximum east coordinates
    east_min = np.floor(np.min(data[:, 1] - data[:, 4]))
    east_max = np.ceil(np.max(data[:, 1] + data[:, 4]))

    # given the minimum and maximum coordinates we can
    # calculate the size of the grid.
    north_size = int(np.ceil(north_max - north_min))
    east_size = int(np.ceil(east_max - east_min))

    # Initialize an empty grid
    grid = np.zeros((north_size, east_size))

    # Populate the grid with obstacles
    for i in range(data.shape[0]):
        north, east, alt, d_north, d_east, d_alt = data[i, :]
        if alt + d_alt + safety_distance > drone_altitude:
            obstacle = [
                int(np.clip(north - d_north - safety_distance - north_min, 0, north_size-1)),
                int(np.clip(north + d_north + safety_distance - north_min, 0, north_size-1)),
                int(np.clip(east - d_east - safety_distance - east_min, 0, east_size-1)),
                int(np.clip(east + d_east + safety_distance - east_min, 0, east_size-1)),
            ]
            grid[obstacle[0]:obstacle[1]+1, obstacle[2]:obstacle[3]+1] = 1

    return grid, int(north_min), int(east_min)


# Assume all actions cost the same.
class Action(Enum):
    """
    An action is represented by a 3 element tuple.

    The first 2 values are the delta of the action relative
    to the current grid position. The third and final value
    is the cost of performing the action.
    """

    WEST =  ( 0.,-1., 1)
    EAST =  ( 0., 1., 1)
    NORTH = (-1., 0., 1)
    SOUTH = ( 1., 0., 1)

    NORTHWEST = (-0.707, -0.707, 1)
    NORTHEAST = (-0.707,  0.707, 1)
    SOUTHWEST = ( 0.707, -0.707, 1)
    SOUTHEAST = ( 0.707,  0.707, 1)

    @property
    def cost(self):
        return self.value[2]

    @property
    def delta(self):
        return (self.value[0], self.value[1])


def valid_actions(grid, current_node):
    """
    Returns a list of valid actions given a grid and current node.
    """
    valid_actions = list(Action)
    n, m = grid.shape[0] - 1, grid.shape[1] - 1
    x, y = current_node

    # check if the node is off the grid or
    # it's an obstacle

    #print('grid shape {}, current node {}'.format(grid.shape, current_node))
    try:
        if x - 1 < 0 or grid[int(round(x - 1)), int(round(y))] == 1:
            valid_actions.remove(Action.NORTH)
            valid_actions.remove(Action.NORTHWEST)
            valid_actions.remove(Action.NORTHEAST)
        if x + 1 > n or grid[int(round(x + 1)), int(round(y))] == 1:
            valid_actions.remove(Action.SOUTH)
            valid_actions.remove(Action.SOUTHWEST)
            valid_actions.remove(Action.SOUTHEAST)
        if y - 1 < 0 or grid[int(round(x)), int(round(y - 1))] == 1:
            valid_actions.remove(Action.WEST)
            valid_actions.remove(Action.NORTHWEST)
            valid_actions.remove(Action.SOUTHWEST)
        if y + 1 > m or grid[int(round(x)), int(round(y + 1))] == 1:
            valid_actions.remove(Action.EAST)
            valid_actions.remove(Action.NORTHEAST)
            valid_actions.remove(Action.SOUTHEAST)
    except ValueError:
        pass

    return valid_actions


def a_star(grid, h, start, goal):

    path = []
    path_cost = 0
    queue = PriorityQueue()
    queue.put((0, start))
    visited = set(start)

    branch = {}
    found = False
    final_goal = start
    while not queue.empty():
        item = queue.get()
        current_node = item[1]
        if current_node == start:
            current_cost = 0.0
        else:
            current_cost = branch[current_node][0]

        dist = np.linalg.norm(np.array(current_node) - np.array(goal))
        if dist < 1.:
            print('Found a path of length {}.'.format(queue.qsize()))
            found = True
            final_goal = current_node
            break
        else:
            for action in valid_actions(grid, current_node):
                # get the tuple representation
                da = action.delta
                next_node = (current_node[0] + da[0], current_node[1] + da[1])
                branch_cost = current_cost + action.cost
                queue_cost = branch_cost + h(next_node, goal)

                # upsample the next node
                upsample_next_node = (int(round(next_node[0] * 2)), int(round(next_node[1] * 2)))
                if upsample_next_node not in visited:                
                    visited.add(upsample_next_node)
                    branch[next_node] = (branch_cost, current_node, action)
                    queue.put((queue_cost, next_node))
             
    if found:
        # retrace steps
        n = final_goal
        path_cost = branch[n][0]
        path.append(final_goal)
        while branch[n][1] != start:
            path.append(branch[n][1])
            n = branch[n][1]
        path.append(branch[n][1])
    else:
        print('**********************')
        print('Failed to find a path!')
        print('**********************') 
    return path[::-1], path_cost



def heuristic(position, goal_position):
    return np.linalg.norm(np.array(position) - np.array(goal_position))


def point(p):
    return np.array([p[0], p[1], 1.]).reshape(1, -1)

def collinearity_check(p1, p2, p3, epsilon=1e-6):
    m = np.concatenate((p1, p2, p3), 0)
    det = np.linalg.det(m)
    return abs(det) < epsilon

def prune_path(path):
    #pruned_path = [p for p in path]
    if len(path) < 3:
        return path

    p1 = path[0]
    p2 = path[1]
    # always have the 1st point
    pruned_path= [p1]
    for i in range(2, len(path)):
        p3 = path[i]
        # epsilon 1e-6 => .1 doesnt matter
        # 1 => 81
        # 10 => 23
        if collinearity_check(point(p1), point(p2), point(p3), 8):
            # save p3 and remove p2
            p2 = p3
        else:
            # save the turning point
            pruned_path.append(p2)
            p1 = p2
            p2 = p3
    # save the last point
    pruned_path.append(p3)
    return pruned_path

