## Project: 3D Motion Planning
![Quad Image](./misc/enroute.png)

---


# Required Steps for a Passing Submission:
1. Load the 2.5D map in the colliders.csv file describing the environment.
2. Discretize the environment into a grid or graph representation.
3. Define the start and goal locations.
4. Perform a search using A* or other search algorithm.
5. Use a collinearity test or ray tracing method (like Bresenham) to remove unnecessary waypoints.
6. Return waypoints in local ECEF coordinates (format for `self.all_waypoints` is [N, E, altitude, heading], where the drone’s start location corresponds to [0, 0, 0, 0].
7. Write it up.
8. Congratulations!  Your Done!

## [Rubric](https://review.udacity.com/#!/rubrics/1534/view) Points
### Here I will consider the rubric points individually and describe how I addressed each point in my implementation.  

---
### Writeup / README

#### 1. Provide a Writeup / README that includes all the rubric points and how you addressed each one.  You can submit your writeup as markdown or pdf.  

You're reading it! Below I describe how I addressed each rubric point and where in my code each point is handled.

### Explain the Starter Code

#### 1. Explain the functionality of what's provided in `motion_planning.py` and `planning_utils.py`
In planning utils, the basic utitlies including building grid, action class, action validation, A star search and etcs.

In motion_planning, it is an event driven flying system which was inherit from the backyard flyer project. On top of the stages in backyard flyer, it also adds the planning stage.


### Implementing Your Path Planning Algorithm

#### 1. Set your global home position
This is actually harder than it should be IMHO. I used a regex to find the floating point numbers. The original format is "lat0 37.792480, lon0 -122.397450" which is not csv format. If we had "lat0, lon0" on 1st row and "37.792480, -122.397450" on the 2nd, it conforms the csv format and would be much easier to read. I ended up finding the regex expression online to achieve this. But surpringly, finding a robust floating point regex expression requires some search and trial and error.


This part is not very intuitive at first place because global home is set through the set_home_position and I guess in the drone class, we later transform all the coordinate realtively to home position. This makes sense while more document might be easier to understand. If I missed anything, please let me know.


#### 2. Set your current local position
To be honest, I am not fullying understanding how it works under the hood. I guessed what happened was that once we set the global lat/lon coordinate, all the gps reading afterwards will be translated to the local coordinate system.


#### 3. Set grid start position from local position
Another not so clear piece to me.


#### 4. Set grid goal position from geodetic coords
Another not so clear piece to me.


#### 5. Modify A* to include diagonal motion (or replace A* altogether)
I added this and the tricky part is to do cost correctly. I tried to add the diagonal cost by firstly adding an integer move. The problem with that is that it actually has larger cost even tough it might be more efficient. The key is to normalize the cost. I ended up make the move continuous, other than discrete. Another potential way is to have a deeper search strategy (e.g. look more steps ahead, like 2 or more). This solution however will be more complicated to implement. So I used the fractional A star algroithm. There are some tradeoff I need to make, e.g. the duplicate step search. I ended up with the upsampling method. There might be better methods out there.


#### 6. Cull waypoints 
Due to time limit, I ended up with the colinearity check. The Bresenham might be a better solution. Will try to revisit later when I got time. (sorry, the famous excuse :-) )


### Execute the flight
#### 1. Does it work?
It works!

### Double check that you've met specifications for each of the [rubric](https://review.udacity.com/#!/rubrics/1534/view) points.
  
# Extra Challenges: Real World Planning

For an extra challenge, consider implementing some of the techniques described in the "Real World Planning" lesson. You could try implementing a vehicle model to take dynamic constraints into account, or implement a replanning method to invoke if you get off course or encounter unexpected obstacles.


