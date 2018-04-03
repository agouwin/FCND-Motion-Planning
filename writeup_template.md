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
I added this and the tricky part is to calculate cost correctly. The default solution only considers 4-neighbors and the result of it is the "blocky" trajectory.

I addressed this by adding the diagonal move (8 neighbors) and their corersponding costs. I firstly just added the integer move (the offset of +/-1). The problem with that is that our current A star algorithm has a search depth of 1. So if we need (1, 1) move, the original 4-neighbor move will be (1, 0) move followed by a (0, 1) move. And the cost will be 2. For the diagonal move, we just need to take (1, 1) with a cost of 1.414. But because of the search dept is only 1, as far as 1 step is concerned, (1, 0) move will have a lower cost than the (1, 1) move. And this is not optimal.

There are different ways to address it. The solution I provided is a simple one and the key is to normalize the cost. So, instead of a (1, 1) move, I do a (0.717, 0.717) move and the cost is 1. The issue with this right out of the box is that we are hashing the discrete position and when we have fractionaly movement, the hashing simply breaks. My solution to that is to upsample the grids by a factor of two. So each step we made, I will check whether the rounding position to the cloest grid of (0.5, 0.5) resultion is occupied or not. This take some extra calculation, but it works reasonably well. The downside is that it will produce more smaller steps which is not an issue if we do pruning afterwards.

Another potential way is to have a deeper search strategy (e.g. look more steps ahead, like 2 or more). This solution however will be more complicated to implement. 


#### 6. Cull waypoints 
In current implementation, we are using simple colinearity check. At each step, three points p1, p2, p3 were checked. p1 is the starting point, p2 is the mid point to check and p3 and the ending point. There are two scenarios:

1. Colinear: In this case, the three points are on the same line and we remove p2 by replacing it with p3;
2. Non-colinear: In this case, we have 3 points not on the same line. We will keep p2 and mark p3 as the new mid point.

Due to time limit, This is the simplest thing we can do. The Bresenham might be a better solution. Will try to revisit later when I got time. (sorry, the famous excuse :-) )


### Execute the flight
#### 1. Does it work?
It works!

### Double check that you've met specifications for each of the [rubric](https://review.udacity.com/#!/rubrics/1534/view) points.
  
# Extra Challenges: Real World Planning

For an extra challenge, consider implementing some of the techniques described in the "Real World Planning" lesson. You could try implementing a vehicle model to take dynamic constraints into account, or implement a replanning method to invoke if you get off course or encounter unexpected obstacles.


