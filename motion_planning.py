import argparse
import time
import msgpack
import csv
import re
from enum import Enum, auto

import numpy as np

from planning_utils import a_star, heuristic, create_grid, prune_path
from udacidrone import Drone
from udacidrone.connection import MavlinkConnection
from udacidrone.messaging import MsgID
from udacidrone.frame_utils import global_to_local, local_to_global


class States(Enum):
    MANUAL = auto()
    ARMING = auto()
    TAKEOFF = auto()
    WAYPOINT = auto()
    LANDING = auto()
    DISARMING = auto()
    PLANNING = auto()


class MotionPlanning(Drone):

    def __init__(self, connection):
        super().__init__(connection)

        self.target_position = np.array([0.0, 0.0, 0.0])
        self.waypoints = []
        self.in_mission = True
        self.check_state = {}

        # initial state
        self.flight_state = States.MANUAL

        # register all your callbacks here
        self.register_callback(MsgID.LOCAL_POSITION, self.local_position_callback)
        self.register_callback(MsgID.LOCAL_VELOCITY, self.velocity_callback)
        self.register_callback(MsgID.STATE, self.state_callback)

    def local_position_callback(self):
        if self.flight_state == States.TAKEOFF:
            if -1.0 * self.local_position[2] > 0.95 * self.target_position[2]:
                self.waypoint_transition()
        elif self.flight_state == States.WAYPOINT:
            if np.linalg.norm(self.target_position[0:2] - self.local_position[0:2]) < 2.0:
                if len(self.waypoints) > 0:
                    self.waypoint_transition()
                else:
                    if np.linalg.norm(self.local_velocity[0:2]) < 1.0:
                        self.landing_transition()

    def velocity_callback(self):
        if self.flight_state == States.LANDING:
            if self.global_position[2] - self.global_home[2] < 0.1:
                if abs(self.local_position[2]) < 0.01:
                    self.disarming_transition()

    def state_callback(self):
        if self.in_mission:
            if self.flight_state == States.MANUAL:
                self.arming_transition()
            elif self.flight_state == States.ARMING:
                if self.armed:
                    self.plan_path()
            elif self.flight_state == States.PLANNING:
                self.takeoff_transition()
            elif self.flight_state == States.DISARMING:
                if ~self.armed & ~self.guided:
                    self.manual_transition()

    def arming_transition(self):
        self.flight_state = States.ARMING
        print("arming transition")
        self.arm()
        self.take_control()

    def takeoff_transition(self):
        self.flight_state = States.TAKEOFF
        print("takeoff transition")
        self.takeoff(self.target_position[2])

    def waypoint_transition(self):
        self.flight_state = States.WAYPOINT
        print("waypoint transition")
        self.target_position = self.waypoints.pop(0)
        print('target position', self.target_position)
        self.cmd_position(self.target_position[0], self.target_position[1], self.target_position[2], self.target_position[3])

    def landing_transition(self):
        self.flight_state = States.LANDING
        print("landing transition")
        self.land()

    def disarming_transition(self):
        self.flight_state = States.DISARMING
        print("disarm transition")
        self.disarm()
        self.release_control()

    def manual_transition(self):
        self.flight_state = States.MANUAL
        print("manual transition")
        self.stop()
        self.in_mission = False

    def send_waypoints(self):
        print("Sending waypoints to simulator ...")
        data = msgpack.dumps(self.waypoints)
        self.connection._master.write(data)

    def plan_path(self):
        self.flight_state = States.PLANNING
        print("Searching for a path ...")
        TARGET_ALTITUDE = 5
        SAFETY_DISTANCE = 5

        self.target_position[2] = TARGET_ALTITUDE

	# read out the data
        reader = csv.reader('colliders.csv', delimiter=',')
        with open('colliders.csv', newline='') as f:
          reader = csv.reader(f)
          row1 = next(reader)  # gets the first line

          # ['lat0 37.792480', ' lon0 -122.397450']
          reg = r'[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?'
          lat0 = float(re.findall(reg, row1[0])[1])
          lon0 = float(re.findall(reg, row1[1])[1])

        # DONE: set home position to (lon0, lat0, 0)
        self.set_home_position(lon0, lat0, 0.)
        print('set global home [{}, {}, {}]'.format(lon0, lat0, 0.))
        #self.set_home_position(0, 0, 0.)

        # DONE: convert to current local position using global_to_local()
        local_position = global_to_local(self.global_position, self.global_home)

        # DONE: retrieve current global position
        print('Current global position {}; local position {}'.format(self.global_position, local_position))

        #self._north = local_position[0]
        print('global home {0}, position {1}, local position {2}'.format(self.global_home, self.global_position,
                                                                         self.local_position))

        # Read in obstacle map
        data = np.loadtxt('colliders.csv', delimiter=',', dtype='Float64', skiprows=2)

        # Define a grid for a particular altitude and safety margin around obstacles
        grid, north_offset, east_offset = create_grid(data, TARGET_ALTITUDE, SAFETY_DISTANCE)
        print("North offset = {}, east offset = {}, grid size {}".format(north_offset, east_offset, grid.shape))

        # Define starting point on the grid (this is just grid center)
        # DONE?: convert start position to current position rather than map center
        grid_start = (int(round(local_position[0])) - north_offset, int(round(local_position[1])) - east_offset)

        # Set goal as some arbitrary position on the grid
        # grid_goal = (10 -north_offset + 10, 10 -east_offset)
        grid_goal = (0, 30)
        for i in range(grid.shape[1]):
            if grid[0, i] == 0:
                grid_goal = (0, i)
        print('Local Start {} and Goal {}, obstacle {}', grid_start, grid_goal, grid[grid_goal[0], grid_goal[1]])

        # DONE: adapt to set goal as latitude / longitude position and convert
        global_goal = local_to_global([grid_goal[0], grid_goal[1], 0], [lon0, lat0, 0])
        print('global goal {}'.format(global_goal))

        # Run A* to find a path from start to goal
        # TODO: add diagonal motions with a cost of sqrt(2) to your A* implementation

        # or move to a different search space such as a graph (not done here)
        path, _ = a_star(grid, heuristic, grid_start, grid_goal)

        pruned_path = prune_path(path)
        print('Intial path length {}; pruned path {}'.format(len(path), len(pruned_path)))

        # TODO: prune path to minimize number of waypoints
        # TODO (if you're feeling ambitious): Try a different approach altogether!

        # Convert path to waypoints
        # waypoints = [[p[0] + north_offset, p[1] + east_offset, TARGET_ALTITUDE, 0] for p in pruned_path]
        waypoints = [[int(round(p[0] + north_offset)), int(round(p[1] + east_offset)), TARGET_ALTITUDE, 0] for p in pruned_path]
        #print('waypoints {}'.format(waypoints))

        # Set self.waypoints
        self.waypoints = waypoints
        # TODO: send waypoints to sim (this is just for visualization of waypoints)
        self.send_waypoints()

    def start(self):
        self.start_log("Logs", "NavLog.txt")

        print("starting connection")
        self.connection.start()

        # Only required if they do threaded
        # while self.in_mission:
        #    pass

        self.stop_log()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5760, help='Port number')
    parser.add_argument('--host', type=str, default='127.0.0.1', help="host address, i.e. '127.0.0.1'")
    args = parser.parse_args()

    conn = MavlinkConnection('tcp:{0}:{1}'.format(args.host, args.port), timeout=60)
    drone = MotionPlanning(conn)
    time.sleep(1)

    drone.start()
