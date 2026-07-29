# EV3Kernel - API Reference

This document compiles all functions and parameters used in writing Mission Scripts.

---

## 1. KINEMATICS & ODOMETRY

<details>
<summary><b>[+] <code>move_straight(distance_cm, max_speed)</code></b></summary>

Commands the robot to drive straight forward or backward using a closed-loop PID controller to keep both wheels synchronized, preventing drifting.

**Parameters:**
* `distance_cm`: The target distance to travel (centimeters). Positive for forward, negative for backward.
* `max_speed`: Maximum top speed (0-100%).

**Example Usage:**
```python
robot.move_straight(50, max_speed=50)   # Drive forward 50 cm at 50% speed
robot.move_straight(-20, max_speed=40)  # Drive backward 20 cm at 40% speed
```
</details>

<details>
<summary><b>[+] <code>turn(angle_deg, max_speed)</code></b></summary>

Performs a point turn where the left and right wheels rotate in opposite directions. Uses PID to precisely synchronize the movement of both wheels.

**Parameters:**
* `angle_deg`: Target angle to turn (Positive = Right, Negative = Left).
* `max_speed`: Maximum turning speed (0-100%).

**Example Usage:**
```python
robot.turn(90, max_speed=40)   # Turn right 90 degrees
robot.turn(-90, max_speed=40)  # Turn left 90 degrees
```
</details>

<details>
<summary><b>[+] <code>pivot_turn(angle_deg, pivot_side, max_speed)</code></b></summary>

Performs a wide pivot turn by locking one wheel in place and rotating the other.

**Parameters:**
* `angle_deg`: Target angle (Positive = Forward Right / Backward Left, Negative = Forward Left / Backward Right).
* `pivot_side`: `'left'` (locks left wheel) or `'right'` (locks right wheel).

**Example Usage:**
```python
robot.pivot_turn(90, pivot_side='right')  # Lock right wheel, pivot forward on left wheel
```
</details>

---

## 2. ALIGNMENT & HOMING

<details>
<summary><b>[+] <code>align_wall(power, time_ms)</code></b></summary>

Reverses into a physical wall to mechanically square the robot. Limits raw PWM power to prevent the motor gears from stripping during the stall.

**Parameters:**
* `power`: Raw voltage/duty cycle to push against the wall (Positive = Forward, Negative = Backward).
* `time_ms`: Time in milliseconds to push against the wall. (e.g., `1500` = 1.5 seconds)

**Example Usage:**
```python
robot.align_wall(power=-50, time_ms=1500)
```
</details>

<details>
<summary><b>[+] <code>align_line(time_ms)</code></b></summary>

Squares the robot perpendicular to a transverse black line using dual light sensors.

**Parameters:**
* `time_ms`: Maximum time allowed for the alignment process.

**Line Squaring Logic:**
The wheel whose sensor detects the black line first will immediately stop and hold, while the other wheel continues rotating until it also detects the line. This perfectly aligns the robot parallel to the line.

<div align="center">
  <img src="./assets/auto_squaring.gif" alt="Auto Squaring Animation" width="600">
  <p><em>Simulated Line Squaring where the left sensor hits the line first and brakes, waiting for the right side to align.</em></p>
</div>

```text
// Independent Line Squaring Logic
if (Left_Sensor_Sees_Black)  -> Stop Left Motor
if (Right_Sensor_Sees_Black) -> Stop Right Motor
```
</details>

---

## 3. SENSOR FUSION & LINE TRACKING (333Hz)

<details>
<summary><b>[+] <code>drive_until_line(speed, align=True)</code></b></summary>

Drives straight forward until both the left and right sensors detect a black line.

**Parameters:**
* `speed`: Movement speed (0-100%).
* `align`: If `True`, automatically calls `align_line()` immediately upon detection to square the robot.
</details>

<details>
<summary><b>[+] <code>track_line(speed, kp, kd)</code></b></summary>

Straddles a black line using two sensors. Utilizes a PD-controller to follow the line smoothly until a transverse intersection is detected by both sensors.

**Parameters:**
* `speed`: Maximum speed while tracking.
* `kp`: Proportional gain (how hard to turn back toward the line).
* `kd`: Derivative gain (damping force to prevent wobbling/overshooting).
</details>

<details>
<summary><b>[+] <code>track_line_distance(distance_cm, speed, kp, kd)</code></b></summary>

Straddles a black line for a highly precise, pre-defined distance (calculated via Encoder fusion with light sensors).

**Parameters:**
* `distance_cm`: Target distance to track the line for (centimeters).
* `speed`: Movement speed.
* `kp`, `kd`: PD control constants.

**Detailed Explanation:**
When executing `robot.track_line_distance(15, speed=40)`, the following happens:
1. The robot reads from both light sensors to maintain its position on the line.
2. Simultaneously, it calculates the distance traveled in real-time using Motor Encoders.
3. Upon reaching exactly **15 centimeters**, the robot aggressively brakes and terminates the tracking sequence.
</details>

<details>
<summary><b>[+] <code>track_line_timer(time_ms, speed)</code></b></summary>

Straddles a black line for a specific duration. Useful for briefly tracking across intersections.

**Parameters:**
* `time_ms`: Duration to track the line in milliseconds. (e.g., `2000` = 2 seconds).
</details>

---

## 4. ACTUATORS / GRIPPERS

<details>
<summary><b>[+] <code>lift_a(angle, speed, power, wait)</code> / <code>lift_d(...)</code></b></summary>

Actuates the robotic arm motor to a target angle while enforcing an actuation (PWM) limit. This prevents gear stripping if the gripper clamps too hard on an object.

**Parameters:**
* `angle`: Target angle (relative to the zero-point).
* `speed`: Speed of the lift mechanism.
* `power`: Maximum allowable power/duty cycle (0-100%) to limit torque.
* `wait`:
  - `True`: **Blocking**. Execution halts until the arm reaches the target angle.
  - `False`: **Async** (Non-blocking). The arm moves in the background while the next line of code executes immediately (ideal for lifting while driving).
</details>

<details>
<summary><b>[+] <code>reset_lift_a(angle)</code> / <code>reset_lift_d(...)</code></b></summary>

Sets the current position of the arm motor as the specified angle. Commonly used during startup or homing to define the mechanical Zero-point.
</details>

<details>
<summary><b>[+] <code>release_a()</code> / <code>release_d()</code></b></summary>

Releases holding torque, allowing the motor to rotate freely (Stop holding / Float).
</details>

---

## 5. SYSTEM / LOW-LEVEL

<details>
<summary><b>[+] <code>drive(left_speed, right_speed)</code></b></summary>

Bypasses the internal Pybricks PID and directly fires raw velocity commands to the motors. Useful for quick, uncalibrated bursts where high precision is not required.
</details>

<details>
<summary><b>[+] <code>stop_drive(hold)</code></b></summary>

Emergency brake for the drive motors.
* `hold=True`: Commands the motors to actively hold their position (Active Hold) to prevent the robot from rolling.
</details>
