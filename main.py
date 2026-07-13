#!/usr/bin/env pybricks-micropython
# EV3 — Pybricks 4.0 beta (https://beta.pybricks.com/)
# My github account: https://github.com/tiw302, My ig account: @tiw3025k_

#              (GRIPPER)        [[TOP VIEW]]
#               [Port A]
#             .----------.
#         S1  | S2    S3 |  S4
#         (o) | (o)  (o) | (o)
#             |          |
#        [B]--| [Port D] |--[C]
#        (L)  |(MAIN ARM)|  (R)
#             |          |
#             '----------'

"""
* port connections:                                                  [ENGLISH]
    port a = front lift motor (gripper)
    port b = left wheel motor (forward = negative run)
    port c = right wheel motor (forward = positive run)
    port d = main arm lift motor (lifts entire a assembly)

    port s1 = sensor 1 (far left)
    port s2 = sensor 2 (mid left)
    port s3 = sensor 3 (mid right)
    port s4 = sensor 4 (far right)

* algorithms & optimizations used (international-level):
    pidv2:         derivative-on-measurement + ema filter + back-calc anti-windup
    trapprofile:   accel -> cruise -> decel (trapezoidal velocity profile)
    deadband comp: compensates for ev3 medium motor stiction at low speeds
    normalized:    maps sensor.reflection() -> [0,100] using real black/white values
    zero-alloc:    method caching to eradicate garbage collection (gc) in hot loops
    memory opt:    uses __slots__ and const() for minimal ram footprint (~200kb)

* pre-match checklist:
    1. update wheel_diameter_mm / axle_track_mm to match the physical robot
    2. run debug.py (down button) to calibrate and hardcode black_raw / white_raw
    3. hardcode center_offset_xx from calibrate_2sensor_offset()
    4. run debug.py (center button) to verify sensor values

.___________________________________________________________________________________________.

* การต่อพอร์ต:                                                        [THAI]
    port A = มอเตอร์ยกของด้านหน้า (gripper/lift front)
    port B = มอเตอร์ล้อซ้าย (เดินหน้า = run ค่าลบ)
    port C = มอเตอร์ล้อขวา (เดินหน้า = run ค่าบวก)
    port D = มอเตอร์ยกแขน A ทั้งชุด

    port S1 = เซ็นเซอร์ 1 (ซ้ายสุด)
    port S2 = เซ็นเซอร์ 2 (ซ้ายกลาง)
    port S3 = เซ็นเซอร์ 3 (ขวากลาง)
    port S4 = เซ็นเซอร์ 4 (ขวาสุด)

* algorithms & optimizations ที่ใช้ (international-level):
    PIDv2:         derivative-on-measurement + ema filter + back-calc anti-windup
    TrapProfile:   accel -> cruise -> decel (trapezoidal velocity profile)
    Deadband Comp: ชดเชย EV3 medium motor stiction ตอนความเร็วต่ำ
    Normalized:    map sensor.reflection() -> [0,100] ด้วยค่า black/white จริง
    Zero-Alloc:    เทคนิค Cache ลบปัญหา Garbage Collection กระตุกตอนหุ่นวิ่ง
    Memory Opt:    รีด RAM ด้วย __slots__ และ const() ทำงานไว ประหยัดแบต

* ก่อนแข่ง:
    1. แก้ WHEEL_DIAMETER_MM / AXLE_TRACK_MM ให้ตรงหุ่น
    2. รัน debug.py (ปุ่มล่าง) เพื่อคาลิเบรต แล้วมาแก้ BLACK_RAW / WHITE_RAW
    3. Hardcode CENTER_OFFSET_xx จาก calibrate_2sensor_offset()
    4. รัน debug.py (ปุ่มกลาง) เพื่อเช็คค่าแสงและเซ็นเซอร์ให้ชัวร์ก่อนแข่ง
"""

import math
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor, ColorSensor
from pybricks.parameters import Port, Stop, Button
from pybricks.tools import StopWatch, wait
from micropython import const

#  _   _    _    ____  ______        ___    ____  _____ 
# | | | |  / \  |  _ \|  _ \ \      / / \  |  _ \| ____|
# | |_| | / _ \ | |_) | | | \ \ /\ / / _ \ | |_) |  _|  
# |  _  |/ ___ \|  _ <| |_| |\ V  V / ___ \|  _ <| |___ 
# |_| |_/_/   \_\_| \_\____/  \_/\_/_/   \_\_| \_\_____|
#
# >> robot hardware configuration
WHEEL_DIAMETER_MM = 56.0       # diameter of the wheels in mm. used for travel distance.
AXLE_TRACK_MM     = 120.0      # distance between wheels in mm. used for turn arc.
WHEEL_CIRC        = math.pi * WHEEL_DIAMETER_MM  # pi * d

#  _____ _   _ _   _ ___ _   _  ____ 
# |_   _| | | | \ | |_ _| \ | |/ ___|
#   | | | | | |  \| || ||  \| | |  _ 
#   | | | |_| | |\  || || |\  | |_| |
#   |_|  \___/|_| \_|___|_| \_|\____|
#
# >> tuning parameters
DISTANCE_CORRECTION = 0.9   # fix slip on straight (1.05 if it drives short)
TURN_CORRECTION     = 1.42  # fix slip on turns   (0.95 if it overturns)
DEADBAND_SPEED      = const(60)    # min power to overcome motor stiction at low speed
WHITE_LIGHT         = const(34)    # average reflection on white surface (calibrate this before match)
BLACK_LIGHT         = const(4)     # average reflection on black line (calibrate this before match)
LINE_EDGE           = (WHITE_LIGHT + BLACK_LIGHT) / 2  # automatic midpoint threshold

def clamp(v, lo, hi):
    if v < lo: return lo
    if v > hi: return hi
    return v

def apply_deadband(speed, deadband=DEADBAND_SPEED):
    """helper: inject deadband power to overcome stiction. for use in mission scripts."""
    if speed > 1: return speed + deadband
    if speed < -1: return speed - deadband
    return 0

class PIDv2:
    # __slots__ eliminates per-instance __dict__ — saves ~50 bytes of RAM per object
    __slots__ = ('kp', 'ki', 'kd', 'integral', 'prev_measurement', 'd_filtered',
                 'integral_limit', 'd_alpha', 'max_out')

    def __init__(self, kp, ki, kd, integral_limit=150, d_alpha=0.25, max_out=None):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.integral = 0.0
        self.prev_measurement = None
        self.d_filtered = 0.0
        self.integral_limit = integral_limit
        self.d_alpha = d_alpha
        self.max_out = max_out
        
    def reset(self):
        self.integral = 0.0
        self.prev_measurement = None
        self.d_filtered = 0.0
        
    def compute(self, error, measurement, dt):
        """
        computes the pid output using derivative on measurement to prevent reference kick.
        formula: output = (kp * error) + (ki * integral) - (kd * (d_measurement / dt))
        includes integral anti-windup to prevent runaway errors during stalls.
        available for use in user mission scripts (e.g. line following).
        """
        if dt <= 0: return 0.0
        p = self.kp * error
        
        integ = self.integral + error * dt
        lim = self.integral_limit
        if integ > lim: self.integral = lim
        elif integ < -lim: self.integral = -lim
        else: self.integral = integ
        
        i = self.ki * self.integral
        
        if self.prev_measurement is None:
            self.prev_measurement = measurement
        d_raw = -(measurement - self.prev_measurement) * (1.0 / dt)
        self.d_filtered = self.d_alpha * d_raw + (1.0 - self.d_alpha) * self.d_filtered
        self.prev_measurement = measurement
        d = self.kd * self.d_filtered
        
        output = p + i + d
        
        if self.max_out is not None and self.ki > 0:
            mo = self.max_out
            if output > mo: clamped = mo
            elif output < -mo: clamped = -mo
            else: clamped = output
            if output != clamped:
                self.integral = (clamped - p - d) / self.ki
                
        return output

class TrapProfile:
    # __slots__ for RAM savings
    __slots__ = ('total', 'min_speed', 'max_speed', 'accel_end', 'decel_start')

    def __init__(self, total_deg, min_speed, max_speed, accel_frac=0.25, decel_frac=0.30):
        self.total = total_deg
        self.min_speed = min_speed
        self.max_speed = max_speed
        self.accel_end = total_deg * accel_frac
        self.decel_start = total_deg * (1.0 - decel_frac)
        
    def speed_at(self, progress):
        """
        generates a trapezoidal velocity profile based on current distance progress.
        phase 1: linearly accelerates from min_speed to max_speed.
        phase 2: cruises at max_speed.
        phase 3: linearly decelerates from max_speed back to min_speed.
        available for use in user mission scripts (e.g. line following with speed control).
        """
        if self.total <= 0: return self.min_speed
        if progress <= self.accel_end:
            t = progress / self.accel_end if self.accel_end > 0 else 1.0
            return self.min_speed + (self.max_speed - self.min_speed) * t
        if progress >= self.decel_start:
            decel_dist = self.total - self.decel_start
            t = (self.total - progress) / decel_dist if decel_dist > 0 else 0.0
            return self.min_speed + (self.max_speed - self.min_speed) * t
        return self.max_speed

class Robot:
    # __slots__: eliminates __dict__ on robot instance — largest single RAM saving
    __slots__ = ('hub', 'left_motor', 'right_motor', 'lift_motor_a', 'lift_motor_d',
                 'sensor_1', 'sensor_2', 'sensor_3', 'sensor_4', 'black_raw', 'white_raw')
#  ██████  ███████ ████████ ██    ██ ██████  
# ██       ██         ██    ██    ██ ██   ██ 
#  █████   █████      ██    ██    ██ ██████  
#      ██  ██         ██    ██    ██ ██      
# ██████   ███████    ██     ██████  ██      
#
# >> setup core (initialization, port and sensor checking)
# >> setup core (ระบบตั้งค่าเริ่มต้น เช็คพอร์ตและเซ็นเซอร์)
    def __init__(self):
        self.hub = EV3Brick()
        # disable default center-button kill so estop routes through stop_drive()
        self.hub.system.set_stop_button(None)
        print("[ROBOT] ------------------------------")
        print("[ROBOT] Initializing Ports...")
        
        self.left_motor   = self._init_motor(Port.B, "Left Motor")
        self.right_motor  = self._init_motor(Port.C, "Right Motor")
        self.lift_motor_a = self._init_motor(Port.A, "Lift A", required=False)
        self.lift_motor_d = self._init_motor(Port.D, "Lift D", required=False)
        
        self.sensor_1 = self._init_sensor(Port.S1, "S1")
        self.sensor_2 = self._init_sensor(Port.S2, "S2")
        self.sensor_3 = self._init_sensor(Port.S3, "S3")
        self.sensor_4 = self._init_sensor(Port.S4, "S4")
        
        print("[ROBOT] All required ports connected!")
        self.check_battery()
        print("[ROBOT] ------------------------------")
        
        self.black_raw = BLACK_LIGHT
        self.white_raw = WHITE_LIGHT

    def _init_motor(self, port, label, required=True):
        try:
            m = Motor(port)
            print(f"[ROBOT]   [OK] {label} ({port})")
            return m
        except Exception:
            print(f"[ROBOT]   [FAIL] {label} ({port})")
            if required:
                self.hub.speaker.beep(200, 500)
                raise
            return None

    def _init_sensor(self, port, label):
        try:
            s = ColorSensor(port)
            print(f"[ROBOT]   [OK] {label} ({port})")
            return s
        except Exception:
            print(f"[ROBOT]   [FAIL] {label} ({port})")
            self.hub.speaker.beep(200, 500)
            raise

# ███    ███  ██████  ██    ██ ███████ ███    ███ ███████ ███    ██ ████████ 
# ████  ████ ██    ██ ██    ██ ██      ████  ████ ██      ████   ██    ██    
# ██ ████ ██ ██    ██ ██    ██ █████   ██ ████ ██ █████   ██ ██  ██    ██    
# ██  ██  ██ ██    ██  ██  ██  ██      ██  ██  ██ ██      ██  ██ ██    ██    
# ██      ██  ██████    ████   ███████ ██      ██ ███████ ██   ████    ██    
#
# >> movement core (drive mechanics, straight motion and turning)
# >> movement core (ระบบขับเคลื่อนล้อซ้ายขวา วิ่งตรง และเลี้ยว)

#  __  __  ___  _   _ ___   ___ _____ ___    _   ___ ___ _  _ _____
# |  \/  |/ _ \| \ / / __| / __|_   _| _ \  /_\ |_ _/ __| || |_   _|
# | |\/| | (_) |\ V /| _|  \__ \ | | |   / / _ \ | | (_ | __ | | |
# |_|  |_|\___/  \_/ |___| |___/ |_| |_|_\/_/ \_\___\___|_||_| |_|
    def move_straight(self, distance_cm, max_speed=40, min_speed=8,
                    kp=0.45, ki=0.8, kd=0.25, accel_frac=0.25, decel_frac=0.30):
        """
        drives straight by synchronizing left and right wheels using a pid controller.
        formula: motor_degrees = (distance_mm / wheel_circumference) * 360 * correction
        it compares encoder differences (left - right) to keep the robot moving perfectly straight.
        """
        distance_mm = distance_cm * 10
        self.log(f"Start: str {distance_cm}cm")
        self.reset_encoders()
        
        # pre-compute all loop-invariant values outside the hot loop (zero runtime alloc)
        max_spd    = max_speed * 10
        min_spd    = min_speed * 10
        spd_range  = max_spd - min_spd
        target     = abs(distance_mm) / WHEEL_CIRC * 360.0 * DISTANCE_CORRECTION
        dirn       = 1 if distance_mm >= 0 else -1
        accel_end  = target * accel_frac
        decel_st   = target * (1.0 - decel_frac)
        decel_dist = target - decel_st
        pid_ilim   = 100.0
        pid_maxout = max_spd * 0.4
        db         = DEADBAND_SPEED
        db_thresh  = min_spd * 1.5
        d_alpha    = 0.2
        d_alpha_i  = 0.8  # 1.0 - d_alpha (pre-computed)
        
        # cache bound method refs — eliminates attribute lookup on every iteration
        la_func      = self.left_motor.angle
        ra_func      = self.right_motor.angle
        l_run        = self.left_motor.run
        r_run        = self.right_motor.run
        lw           = StopWatch()
        lw_time      = lw.time    # cache StopWatch methods too
        lw_reset     = lw.reset
        
        # pid state as plain locals — local var access is fastest in micropython
        pid_integral = 0.0
        pid_prev     = None
        pid_d_filt   = 0.0
        
        while True:
            la       = -la_func()
            ra       = ra_func()
            progress = (abs(la) + abs(ra)) * 0.5
            
            if progress >= target: break
            
            # real dt via multiply (faster than divide by 1000)
            dt = lw_time() * 0.001
            lw_reset()
            if dt <= 0.0: dt = 0.01
            
            # inline trapezoid profile — no function call overhead
            if progress <= accel_end:
                t    = progress / accel_end if accel_end > 0.0 else 1.0
                base = (min_spd + spd_range * t) * dirn
            elif progress >= decel_st:
                t    = (target - progress) / decel_dist if decel_dist > 0.0 else 0.0
                base = (min_spd + spd_range * t) * dirn
            else:
                base = max_spd * dirn
                
            # inline pid: derivative-on-measurement + ema + back-calc anti-windup
            enc_diff = la - ra
            
            integ = pid_integral + enc_diff * dt
            if integ > pid_ilim: pid_integral = pid_ilim
            elif integ < -pid_ilim: pid_integral = -pid_ilim
            else: pid_integral = integ
            
            if pid_prev is None: pid_prev = enc_diff
            d_raw      = -(enc_diff - pid_prev) * (1.0 / dt)
            pid_d_filt = d_alpha * d_raw + d_alpha_i * pid_d_filt
            pid_prev   = enc_diff
            
            p_out      = kp * enc_diff
            i_out      = ki * pid_integral
            d_out      = kd * pid_d_filt
            correction = p_out + i_out + d_out
            
            # back-calc anti-windup — inline, no function call
            if ki > 0.0:
                if correction > pid_maxout: clamped = pid_maxout
                elif correction < -pid_maxout: clamped = -pid_maxout
                else: clamped = correction
                if correction != clamped:
                    pid_integral = (clamped - p_out - d_out) / ki
                    
            # inline speed clamp
            l = base - correction
            if l > max_spd: l = max_spd
            elif l < -max_spd: l = -max_spd
            r = base + correction
            if r > max_spd: r = max_spd
            elif r < -max_spd: r = -max_spd
            
            # inline deadband compensation — avoids function call overhead
            if abs(l) < db_thresh:
                if l > 1: l += db
                elif l < -1: l -= db
                else: l = 0
            if abs(r) < db_thresh:
                if r > 1: r += db
                elif r < -1: r -= db
                else: r = 0
                
            l_run(-l)
            r_run(r)
            wait(10)
            
        self.stop_drive()
        self.log("Done: str")

#  _____ _   _ ___ _  _
# |_   _| | | | _ \ \| |
#   | | | |_| |   / .` |
#   |_|  \___/|_|_\_|\_|
    def turn(self, angle_deg, max_speed=20, min_speed=6,
            kp=1.2, ki=0.01, kd=0.3, accel_frac=0.30, decel_frac=0.35):
        """
        performs a precise point-turn by spinning wheels in opposite directions.
        formula: arc_length = (turn_angle / 360) * (pi * axle_track_mm)
                 target_degrees = (arc_length / wheel_circumference) * 360
        syncs wheels via pid so that abs(left) - abs(right) remains 0.
        """
        self.log(f"Start: turn {angle_deg}d")
        self.reset_encoders()

        # pre-compute all loop-invariant values
        max_spd    = max_speed * 10
        min_spd    = min_speed * 10
        spd_range  = max_spd - min_spd
        arc_mm     = abs(angle_deg) / 360.0 * (math.pi * AXLE_TRACK_MM)
        target     = arc_mm / WHEEL_CIRC * 360.0 * TURN_CORRECTION
        dirn       = 1 if angle_deg >= 0 else -1
        accel_end  = target * accel_frac
        decel_st   = target * (1.0 - decel_frac)
        decel_dist = target - decel_st
        pid_ilim   = 80.0
        d_alpha    = 0.2
        d_alpha_i  = 0.8
        
        # cache bound method refs
        la_func     = self.left_motor.angle
        ra_func     = self.right_motor.angle
        l_run       = self.left_motor.run
        r_run       = self.right_motor.run
        lw          = StopWatch()
        lw_time     = lw.time
        lw_reset    = lw.reset
        
        # pid state as locals
        pid_integral = 0.0
        pid_prev     = None
        pid_d_filt   = 0.0
        
        while True:
            la       = -la_func()
            ra       = ra_func()
            progress = (abs(la) + abs(ra)) * 0.5
            
            if progress >= target: break
            
            dt = lw_time() * 0.001
            lw_reset()
            if dt <= 0.0: dt = 0.01
            
            # inline trapezoid profile
            if progress <= accel_end:
                t    = progress / accel_end if accel_end > 0.0 else 1.0
                base = min_spd + spd_range * t
            elif progress >= decel_st:
                t    = (target - progress) / decel_dist if decel_dist > 0.0 else 0.0
                base = min_spd + spd_range * t
            else:
                base = max_spd
                
            # inline pid
            sync_err = abs(la) - abs(ra)
            
            integ = pid_integral + sync_err * dt
            if integ > pid_ilim: pid_integral = pid_ilim
            elif integ < -pid_ilim: pid_integral = -pid_ilim
            else: pid_integral = integ
            
            if pid_prev is None: pid_prev = sync_err
            d_raw      = -(sync_err - pid_prev) * (1.0 / dt)
            pid_d_filt = d_alpha * d_raw + d_alpha_i * pid_d_filt
            pid_prev   = sync_err
            
            correction = kp * sync_err + ki * pid_integral + kd * pid_d_filt
            
            # clamp to [0, max]: prevents wheel reversing when correction is large
            l = base + correction
            if l > max_spd: l = max_spd
            elif l < 0: l = 0
            r = base - correction
            if r > max_spd: r = max_spd
            elif r < 0: r = 0
            
            l_run(-(dirn * l))
            r_run(-dirn * r)
            wait(10)

        self.stop_drive()
        self.log("Done: turn")

    def pivot_turn(self, angle_deg, pivot_side='right', max_speed=100, min_speed=10, accel_frac=0.2, decel_frac=0.2):
        """
        turns the robot by moving only one wheel (pivot turn) with trapezoidal profile.
        angle_deg: positive for clockwise, negative for counter-clockwise.
        pivot_side: 'right' (hold right wheel, move left) or 'left' (hold left wheel, move right).
        """
        self.log(f"Start: pivot turn {angle_deg}d on {pivot_side}")
        self.reset_encoders()

        # distance is exactly 2x that of a normal point turn.
        max_spd    = max_speed * 10
        min_spd    = min_speed * 10
        spd_range  = max_spd - min_spd
        arc_mm     = abs(angle_deg) / 360.0 * (2.0 * math.pi * AXLE_TRACK_MM)
        target     = arc_mm / WHEEL_CIRC * 360.0 * TURN_CORRECTION
        dirn       = 1 if angle_deg >= 0 else -1
        accel_end  = target * accel_frac
        decel_st   = target * (1.0 - decel_frac)
        decel_dist = target - decel_st
        
        la_func     = self.left_motor.angle
        ra_func     = self.right_motor.angle
        
        if pivot_side == 'right':
            active_run = self.left_motor.run
            active_ang = la_func
            self.right_motor.hold()
            run_sign = -dirn
        else:
            active_run = self.right_motor.run
            active_ang = ra_func
            self.left_motor.hold()
            run_sign = -dirn

        while True:
            progress = abs(active_ang())
            
            if progress >= target: break
                
            # inline trapezoid profile
            if progress <= accel_end:
                t    = progress / accel_end if accel_end > 0.0 else 1.0
                base = min_spd + spd_range * t
            elif progress >= decel_st:
                t    = (target - progress) / decel_dist if decel_dist > 0.0 else 0.0
                base = min_spd + spd_range * t
            else:
                base = max_spd
                
            active_run(run_sign * base)
            wait(10)

        self.stop_drive()
        self.log("Done: pivot turn")

    def drive(self, left_speed, right_speed):
        self.left_motor.run(-left_speed)
        self.right_motor.run(right_speed)

#    _   _    ___ ___ _  _   __      __ _   _    _
#   /_\ | |  |_ _/ __| \| |  \ \    / //_\ | |  | |
#  / _ \| |__ | | (_ | .` |   \ \/\/ // _ \| |__| |__
# /_/ \_\____|___\___|_|\_|    \_/\_//_/ \_\____|____|
    def align_wall(self, power, time_ms, hold=True, kp=0.5):
        """
        runs the robot into a wall using PID sync to stay straight,
        but limits raw power to prevent violent stalling.
        power: raw duty cycle power -100 to 100 (positive for forward).
        time_ms: time in milliseconds to push against the wall.
        hold: if True, applies active hold after stalling.
        """
        self.log(f"Start: align wall {power}% for {time_ms}ms")
        self.reset_encoders()
        
        la_func = self.left_motor.angle
        ra_func = self.right_motor.angle
        max_pwr = abs(power)
        
        watch = StopWatch()
        while watch.time() < time_ms:
            la = -la_func()
            ra = ra_func()
            
            # basic proportional sync to stay perfectly straight
            sync_err = la - ra
            correction = kp * sync_err
            
            l = power - correction
            r = power + correction
            
            # clamp power to prevent ramping up during stall
            if l > max_pwr: l = max_pwr
            elif l < -max_pwr: l = -max_pwr
            if r > max_pwr: r = max_pwr
            elif r < -max_pwr: r = -max_pwr
            
            self.left_motor.dc(-l)
            self.right_motor.dc(r)
            
            wait(10)
            
        self.stop_drive(hold)
        self.log("Done: align wall")

#  ___  ___ _____   __ ___   _   _ _  _ _____ ___ _    _    ___ _  _ ___
# |   \| _ \_ _\ \ / /| __| | | | | \| |_   _|_ _| |  | |  |_ _| \| | __|
# | |) |   /| | \ V / | _|  | |_| | .` | | |  | || |__| |__ | || .` | _|
# |___/|_|_\___| \_/  |___|  \___/|_|\_| |_| |___|____|____|___|_|\_|___|
    def drive_until_line(self, speed=40, threshold=LINE_EDGE, left_sensor='2', right_sensor='3', align=True, align_time=1000, align_target=LINE_EDGE, align_kp=3.0):
        """
        drives straight until BOTH sensors detect the line (handles steep angles).
        speed: speed percentage (0-100).
        threshold: light value to consider as black (usually 30 or below).
        align: if True, automatically calls align_line() after stopping.
        align_time: milliseconds to spend aligning if align=True.
        align_target: target light value for aligning (edge of the line).
        align_kp: proportional gain for aligning.
        """
        self.log(f"Start: drive until line at speed {speed}%")
        ls = getattr(self, f"sensor_{left_sensor}")
        rs = getattr(self, f"sensor_{right_sensor}")
        ls_ref = ls.reflection
        rs_ref = rs.reflection
        
        l_run = self.left_motor.run
        r_run = self.right_motor.run
        
        target_spd = speed * 10
        l_run(-target_spd)
        r_run(target_spd)
        
        l_found = False
        r_found = False
        
        # wait until both sensors detect the line
        while not (l_found and r_found):
            
            # if left hits the line first, hold left motor and wait for right
            if not l_found and ls_ref() <= threshold:
                self.left_motor.hold()
                l_found = True
                
            # if right hits the line first, hold right motor and wait for left
            if not r_found and rs_ref() <= threshold:
                self.right_motor.hold()
                r_found = True
                
            wait(10)
            
        self.stop_drive(hold=True)
        
        if align:
            self.align_line(target_val=align_target, kp=align_kp, time_ms=align_time, left_sensor=left_sensor, right_sensor=right_sensor)
            
        self.log("Done: drive until line")

#  _____ ___    _   ___ _  _   _    ___ _  _ ___
# |_   _| _ \  /_\ / __| |/ / | |  |_ _| \| | __|
#   | | |   / / _ \ (__| ' <  | |__ | || .` | _|
#   |_| |_|_\/_/ \_\___|_|\_\ |____|___|_|\_|___|
    def track_line(self, speed=40, kp=1.5, kd=0.5, threshold=LINE_EDGE, left_sensor='2', right_sensor='3'):
        """
        follows a line by keeping it between two sensors (straddling).
        stops when BOTH sensors detect black (intersection).
        uses pd-controller (proportional-derivative) for extremely smooth tracking.
        speed: speed percentage (0-100).
        kp: proportional gain (how hard to turn towards the line).
        kd: derivative gain (how hard to brake to prevent wiggling/overshooting).
        threshold: light value to consider as black for intersection.
        """
        self.log(f"Start: track line at speed {speed}%")
        ls = getattr(self, f"sensor_{left_sensor}")
        rs = getattr(self, f"sensor_{right_sensor}")
        ls_ref = ls.reflection
        rs_ref = rs.reflection
        
        l_run = self.left_motor.run
        r_run = self.right_motor.run
        
        base_spd = speed * 10
        last_error = 0
        
        while True:
            
            l_val = ls_ref()
            r_val = rs_ref()
            
            # intersection detection: both sensors see black
            if l_val <= threshold and r_val <= threshold:
                break
                
            # pd calculation (straddling line)
            error = l_val - r_val
            derivative = error - last_error
            turn = (error * kp) + (derivative * kd)
            
            l_spd = base_spd + turn
            r_spd = base_spd - turn
            
            l_run(-l_spd)
            r_run(r_spd)
            
            last_error = error
            wait(10)
            
        self.stop_drive(hold=True)
        self.log("Done: track line (intersection detected)")

#    _   _    ___ ___ _  _   _    ___ _  _ ___
#   /_\ | |  |_ _/ __| \| | | |  |_ _| \| | __|
#  / _ \| |__ | | (_ | .` | | |__ | || .` | _|
# /_/ \_\____|___\___|_|\_| |____|___|_|\_|___|
    def align_line(self, target_val=LINE_EDGE, kp=3.0, time_ms=1500, left_sensor='2', right_sensor='3', hold=True):
        """
        aligns the robot perpendicularly to a line using independent proportional controllers.
        it actively seeks the edge of the line to prevent overshoot.
        target_val: target light value (usually 50 for the edge of black/white).
        kp: proportional gain for correcting overshoot/undershoot (use higher values for run()).
        time_ms: time in milliseconds to run the alignment loop.
        left_sensor/right_sensor: '1', '2', '3', or '4'.
        hold: if True, applies active hold after aligning.
        """
        self.log(f"Start: align line (target {target_val}) for {time_ms}ms")
        
        # map string to actual sensor objects
        ls = getattr(self, f"sensor_{left_sensor}")
        rs = getattr(self, f"sensor_{right_sensor}")
        
        # cache methods to eliminate loop lookup overhead (saves RAM/CPU)
        ls_ref = ls.reflection
        rs_ref = rs.reflection
        l_run = self.left_motor.run
        r_run = self.right_motor.run
        
        watch = StopWatch()
        while watch.time() < time_ms:
            
            l_val = ls_ref()
            r_val = rs_ref()
            
            # calculate error from the edge of the line
            # if we see 90 (white), error = 40 (move forward)
            # if we see 10 (black), error = -40 (move backward to correct overshoot!)
            l_err = l_val - target_val
            r_err = r_val - target_val
            
            l_spd = l_err * kp
            r_spd = r_err * kp
            
            # clamp max speed in deg/s to prevent violent wiggling
            if l_spd > 250: l_spd = 250
            elif l_spd < -250: l_spd = -250
            if r_spd > 250: r_spd = 250
            elif r_spd < -250: r_spd = -250
            
            # apply speed (left is inverted)
            l_run(-l_spd)
            r_run(r_spd)
            
            wait(10)
            
        self.stop_drive(hold)
        self.log("Done: align line")
        
    def stop_drive(self, hold=True):
        if hold:
            self.left_motor.hold()
            self.right_motor.hold()
        else:
            self.left_motor.brake()
            self.right_motor.brake()

# ██      ██ ███████ ████████ 
# ██      ██ ██         ██    
# ██      ██ █████      ██    
# ██      ██ ██         ██    
# ███████ ██ ██         ██    
#
# >> lift core (robotic arm mechanisms for gripping and lifting)
# >> lift core (ระบบแขนกลสำหรับคีบและยกสิ่งของ)
    def lift_a(self, speed=50, power=20):
        self.log(f"Start: Lift A (P={power})")
        if self.lift_motor_a:
            self.lift_motor_a.run_until_stalled(speed * 10, then=Stop.HOLD, duty_limit=power)
        self.log("Done: Lift A")

    def lift_d(self, speed=50, power=70):
        self.log(f"Start: Lift D (P={power})")
        if self.lift_motor_d:
            self.lift_motor_d.run_until_stalled(speed * 10, then=Stop.HOLD, duty_limit=power)
        self.log("Done: Lift D")

    def release_a(self):
        self.log("Release A")
        if self.lift_motor_a: self.lift_motor_a.stop()

    def release_d(self):
        self.log("Release D")
        if self.lift_motor_d: self.lift_motor_d.stop()

#  ██████  ███████ ███    ██  ██████   ██████  ██████   ██████  
# ██       ██      ████   ██ ██       ██    ██ ██   ██ ██       
#  █████   █████   ██ ██  ██  █████   ██    ██ ██████   █████   
#      ██  ██      ██  ██ ██      ██  ██    ██ ██   ██      ██  
# ██████   ███████ ██   ████ ██████    ██████  ██   ██ ██████   
#
# >> sensor core (light values, calibration, and line detection)
# >> sensor core (ระบบจัดการค่าแสง คาลิเบรต และเช็คเส้น)
    def calibrate_2sensor_offset(self, seconds=2):
        self.log("Start: Calibrating Offset")
        self.hub.speaker.beep(500, 150)
        watch = StopWatch()
        total, count = 0.0, 0
        while watch.time() < seconds * 1000:
            total += self.sensor_3.reflection() - self.sensor_4.reflection()
            count += 1
            wait(10)

        self.hub.speaker.beep(800, 150)
        offset = total / count if count > 0 else 0.0
        self.log(f"Done: OFFSET {offset:.2f}")
        return offset

    def normalize(self, raw):
        """
        maps raw sensor reflection values to a 0-100 percentage.
        formula: result = ((raw - black_raw) / (white_raw - black_raw)) * 100
        """
        if self.white_raw == self.black_raw: return 50
        return clamp((raw - self.black_raw) / (self.white_raw - self.black_raw) * 100, 0, 100)

    def check_border(self, threshold=15):
        return self.sensor_4.reflection() < threshold

    def check_intersection(self, threshold=15):
        return self.sensor_3.reflection() < threshold and self.sensor_4.reflection() < threshold

    def dist_stop(self, target_cm):
        """
        creates a lambda condition that returns true when the target distance is reached.
        formula: target_deg = (target_mm / wheel_circumference) * 360
        useful for stopping loops dynamically when driving a specific distance.
        """
        target_mm  = target_cm * 10
        self.reset_encoders()
        target_deg = (target_mm / WHEEL_CIRC) * 360 * DISTANCE_CORRECTION
        return lambda: self.avg_angle() >= target_deg

# ██    ██ ████████ ██ ██      ██ ████████ ███████ ███████ 
# ██    ██    ██    ██ ██      ██    ██    ██      ██      
# ██    ██    ██    ██ ██      ██    ██    █████   ███████ 
# ██    ██    ██    ██ ██      ██    ██    ██           ██ 
#  ██████     ██    ██ ███████ ██    ██    ███████ ███████ 
#
# >> utility core (helper functions, encoders, printing)
# >> utility core (ฟังก์ชันช่วยเหลือย่อย เช็คเอนโค้ดเดอร์ สั่ง print)
    def reset_encoders(self):
        self.left_motor.reset_angle(0)
        self.right_motor.reset_angle(0)

    def get_left_angle(self): return -self.left_motor.angle()
    def get_right_angle(self): return self.right_motor.angle()
    def avg_angle(self): return (abs(self.get_left_angle()) + abs(self.get_right_angle())) / 2

    def check_battery(self):
        """
        reads the ev3 battery voltage and current using pybricks 4.0 api.
        formula: percent = ((voltage - 7.0v) / (8.2v - 7.0v)) * 100
        """
        volts   = self.hub.battery.voltage() / 1000.0
        amps    = self.hub.battery.current() / 1000.0
        percent = clamp((volts - 7.0) / (8.2 - 7.0) * 100, 0, 100)
        self.log(f"BATTERY: {volts:.2f}V ({percent:.0f}%) | CURRENT: {amps:.2f}A")

    def log(self, text):
        print(f"[ROBOT] {text}")

#  __  __    _    ___ _   _   _     ___   ___  ____  
# |  \/  |  / \  |_ _| \ | | | |   / _ \ / _ \|  _ \ 
# | |\/| | / _ \  | ||  \| | | |  | | | | | | | |_) |
# | |  | |/ ___ \ | || |\  | | |__| |_| | |_| |  __/ 
# |_|  |_/_/   \_\___|_| \_| |_____\___/ \___/|_|    
#
# >> main execution (mission scripts and logic)
# >> main execution (โค้ดสำหรับรันภารกิจจริง)
if __name__ == "__main__":
    robot = Robot()
    robot.hub.speaker.beep(1047, 200)
    wait(100)
    robot.hub.speaker.beep(1319, 300)
    #   * ===============================================
    #   *  CHEAT SHEET: ตัวอย่างการเรียกใช้ทุกฟังก์ชัน
    #   * ===============================================
        # 1. การเคลื่อนที่พื้นฐาน (basic movements)
        # robot.move_straight(50, max_speed=50)         # วิ่งตรง 50 ซม. ความเร็ว 50 (move straight 50 cm at speed 50)
        # robot.move_straight(-20, max_speed=40)        # ถอยหลัง 20 ซม. (move backward 20 cm)
        # robot.turn(90, max_speed=40)                  # เลี้ยวขวา 90 องศา (point turn right 90 degrees)
        # robot.turn(-90, max_speed=40)                 # เลี้ยวซ้าย 90 องศา (point turn left 90 degrees)
        
        # 2. การเลี้ยวแบบวงกว้าง (pivot turn)
        # robot.pivot_turn(90, pivot_side='right')      # ล้อขวาหยุดนิ่ง ล้อซ้ายเดินหน้า (pivot turn right)
        # robot.pivot_turn(-90, pivot_side='left')      # ล้อซ้ายหยุดนิ่ง ล้อขวาถอยหลัง (pivot turn backward left)
        
        # 3. การชนกำแพงตั้งลำ (wall squaring)
        # robot.align_wall(power=-50, time_ms=1500)     # ถอยชนกำแพงด้วยพลัง -50 เป็นเวลา 1.5 วิ (square against wall for 1.5s)
        
        # 4. การจัดการเซ็นเซอร์แสง (line & sensors)
        # robot.drive_until_line(speed=40, align=True)  # วิ่งไปหาเส้นดำ เจอแล้วเทียบเส้นให้ตรงอัตโนมัติ (drive until black line and auto-align)
        # robot.align_line(time_ms=1500)                # สั่งเทียบเส้นดำเฉยๆ เป็นเวลา 1.5 วิ (align to the line for 1.5s)
        
        # หมายเหตุ: track_line ตอนนี้เป็นลูปอนันต์ ต้องปรับแก้ถ้าจะใช้ในภารกิจจริง (note: track_line is currently an infinite loop)
        # robot.track_line(speed=40, kp=1.5, kd=0.5) 
        
        # 5. การบังคับมอเตอร์แขนกล (grippers)
        # robot.lift_d(speed=80, power=80)              # ยกแขน D ลงคีบด้วยแรงดัน 80% (lower arm D to grip)
        # robot.release_d()                             # ปล่อยแขน D พักมอเตอร์ (release arm D motor)
        # robot.lift_a(speed=50, power=40)              # ยกแขน A ด้วยแรงดัน 40% (lift arm A)
        # robot.release_a()                             # ปล่อยแขน A พักมอเตอร์ (release arm A motor)
        
        # 6. คำสั่งอื่นๆ (misc)
        # robot.drive(300, 300)                         # สั่งมอเตอร์วิ่งตรงๆ ความเร็ว 300 องศา/วิ (drive motors raw at 300 deg/s)
        # robot.stop_drive(hold=True)                   # สั่งเบรกและล็อกล้อ (stop and hold wheels)
        # robot.check_battery()                         # เช็คแบตเตอรี่พิมพ์ออกจอคอม (print battery status to console)
    
    #   * ===============================================
    #   *  RUN: รันตรงนี้
    #   * ===============================================
    robot.check_battery()
    wait(500)
