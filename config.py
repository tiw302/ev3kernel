#!/usr/bin/env pybricks-micropython
# EV3 — Pybricks 4.0 beta (https://beta.pybricks.com/)
# My github account: https://github.com/tiw302, My ig account: @tiw3025k_

# ?             (GRIPPER)        [[TOP VIEW]]
# ?              [Port A]
# ?            .----------.
# ?        S1  | S2    S3 |  S4
# ?        (o) | (o)  (o) | (o)
# ?            |          |
# ?       [B]--| [Port D] |--[C]
# ?       (L)  |(MAIN ARM)|  (R)
# ?            |          |
# ?            '----------'
import math
from micropython import const

#  _   _    _    ____  ______        ___    ____  _____
# | | | |  / \  |  _ \|  _ \ \      / / \  |  _ \| ____|
# | |_| | / _ \ | |_) | | | \ \ /\ / / _ \ | |_) |  _|
# |  _  |/ ___ \|  _ <| |_| |\ V  V / ___ \|  _ <| |___
# |_| |_/_/   \_\_| \_\____/  \_/\_/_/   \_\_| \_\_____|
#
# >> robot hardware configuration
WHEEL_DIAMETER_MM = 56.0  # diameter of the wheels in mm. used for travel distance.
# เส้นผ่านศูนย์กลางล้อ (มม.) ใช้คำนวณระยะทาง
AXLE_TRACK_MM = 120.0  # distance between wheels in mm. used for turn arc.
# ระยะห่างระหว่างล้อซ้าย-ขวา (มม.) ใช้คำนวณวงเลี้ยว
WHEEL_CIRC = math.pi * WHEEL_DIAMETER_MM

#  _____ _   _ _   _ ___ _   _  ____
# |_   _| | | | \ | |_ _| \ | |/ ___|
#   | | | | | |  \| || ||  \| | |  _
#   | | | |_| | |\  || || |\  | |_| |
#   |_|  \___/|_| \_|___|_| \_|\____|
#
# >> tuning parameters
DISTANCE_CORRECTION = 0.9  # fix slip on straight
# ตัวคูณชดเชยระยะทาง
TURN_CORRECTION = 1.45  # fix slip on turns
# ตัวคูณชดเชยองศาเลี้ยว
DEADBAND_SPEED = const(60)  # min power to overcome motor stiction at low speed
# พลังงานขั้นต่ำเพื่อเอาชนะความฝืดมอเตอร์ตอนออกตัว

# * calibrate this before match via debug.py (ต้องคาลิเบรตใหม่ก่อนแข่งเสมอ ผ่านไฟล์ debug.py)
WHITE_LIGHT = const(31)  # average reflection on white surface
# ค่าความสว่างพื้นสีขาว
BLACK_LIGHT = const(3)  # average reflection on black line
# ค่าความมืดเส้นสีดำ
LINE_EDGE = (WHITE_LIGHT + BLACK_LIGHT) / 2  # automatic midpoint threshold
# คำนวณค่ากึ่งกลางอัตโนมัติ

#  _____ _   _ _   _  ____ _____ ___ ___  _   _ ____
# |  ___| | | | \ | |/ ___|_   _|_ _/ _ \| \ | / ___|
# | |_  | | | |  \| | |     | |  | | | | |  \| \___ \
# |  _| | |_| | |\  | |___  | |  | | |_| | |\  |___) |
# |_|    \___/|_| \_|\____| |_| |___\___/|_| \_|____/
#
# >> Function-Specific Configurations
# * =====================================================================================
# * COMMON PARAMETERS / พารามิเตอร์ที่ใช้ร่วมกัน
# * =====================================================================================
# speed_start: initial speed when seeking the line or starting
#              ความเร็วตอนเริ่มต้นเดินหาเส้น หรือตอนออกตัว
# speed_max:   maximum cruising speed
#              ความเร็วสูงสุดในตอนวิ่งเกาะเส้น
# speed_end:   final speed for stopping, timeout, or crawling for maximum alignment
#              ความเร็วตอนใกล้ถึงเป้าหมาย, ใกล้หมดเวลา, หรือค่อยๆ ไถไปเทียบเส้น
# accel_frac:  fraction of distance/time used for acceleration (e.g. .2 = first 20%)
#              สัดส่วนระยะทาง/เวลา ที่ใช้เร่งความเร็ว (เช่น .2 = 20% แรก)
# decel_frac:  fraction of distance/time used for deceleration (e.g. .2 = last 20%)
#              สัดส่วนระยะทาง/เวลา ที่ใช้ชะลอความเร็ว (เช่น .2 = 20% สุดท้าย)
# * =====================================================================================

# used for configuring line tracking until cross intersection is detected
# ใช้สำหรับตั้งค่าการวิ่งเกาะเส้นจนกว่าจะเจอเส้นตัดขวาง
TRACK_LINE_CFG = {"speed": 40, "kp": 0.75, "kd": 6.5, "threshold": LINE_EDGE}

# used for configuring line tracking by distance (cm)
# ใช้สำหรับตั้งค่าการวิ่งเกาะเส้นแบบกำหนดระยะทาง (เซนติเมตร)
TRACK_LINE_DISTANCE_CFG = {"speed": 40, "kp": 0.1, "kd": 3.1}

# used for configuring line tracking by time (sec)
# ใช้สำหรับตั้งค่าการวิ่งเกาะเส้นแบบจับเวลา (วินาที)
TRACK_LINE_TIMER_CFG = {
    "speed": 40,
    "kp": 0.75,
    "kd": 0.5,
}

# used for aligning the robot perpendicular to a cross line
# ใช้สำหรับเทียบให้หุ่นยนต์ตั้งฉากกับเส้น
ALIGN_LINE_CFG = {
    "speed_start": 30,
    "speed_end": 15,
    "target_val": 15,
    "kp": 1.0,
    "time_sec": 1,
}

# used for basic straight movement
# ใช้สำหรับตั้งค่าการวิ่งตรงแบบพื้นฐาน
MOVE_STRAIGHT_CFG = {
    "speed_start": 20,
    "speed_max": 50,
    "speed_end": 20,
    "kp": 0.85,
    "ki": 0.0,
    "kd": 5.5,
    "accel_frac": 0.25,
    "decel_frac": 0.30,
}

# used for turning (gyro/encoder based)
# ใช้สำหรับตั้งค่าการเลี้ยว
TURN_CFG = {
    "speed_start": 30,
    "speed_max": 40,
    "speed_end": 15,
    "kp": 0.11,
    "ki": 0.0,
    "kd": 15,
    "accel_frac": 0.30,
    "decel_frac": 0.35,
}

# used for lifting arm/gripper
# ใช้สำหรับตั้งค่าการยกแขน/คีบ
LIFT_CFG = {"speed": 100}
