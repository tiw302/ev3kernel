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

from ev3kernel import Robot, wait

# ███    ███  █████  ██ ███    ██   ██       ██████   ██████  ███████
# ████  ████ ██   ██ ██ ████   ██   ██      ██    ██ ██    ██ ██    ██
# ██ ████ ██ ███████ ██ ██ ██  ██   ██      ██    ██ ██    ██ ███████
# ██  ██  ██ ██   ██ ██ ██  ██ ██   ██      ██    ██ ██    ██ ██
# ██      ██ ██   ██ ██ ██   ████   ███████  ██████   ██████  ██
#
# >> main execution (mission scripts and logic)
# >> main execution (โค้ดสำหรับ run)

"""
    for english documentation, please read: docs/API_REFERENCE.md
    คู่มือภาษาไทยอธิบายพารามิเตอร์อย่างละเอียด: docs/API_REFERENCE_TH.md
"""

if __name__ == "__main__":
    robot = Robot()
    robot.check_battery()
    wait(500)
    robot.hub.speaker.beep(1047, 200)
    wait(15)
    robot.hub.speaker.beep(1319, 300)
    wait(15)
    robot.reset_lift_a(0)
    robot.reset_lift_d(0)
    try:
        # ! .______________________________________________________________________________________.
        # *  ____  _   _ _   _
        # * |  _ \| | | | \ | |
        # * | |_) | | | |  \| |
        # * |  _ <| |_| | |\  |
        # * |_| \_\____/|_| \_|
        # * >> run: write your robot logic and mission code here!!

        robot.lift_d(90)
        wait(1000)
        robot.lift_d(0)
        wait(1000)

        # ! ._______________________________________________________________________________________.
        pass
    #  _______  _____ _____
    # | ____\ \/ /_ _|_   _|
    # |  _|  \  / | |  | |
    # | |___ /  \ | |  | |
    # |_____/_/\_\___| |_|
    # >> stop robot (program exit)
    except SystemExit:
        robot.hub.speaker.beep(800, 200)
        robot.hub.screen.clear()
        robot.hub.screen.print("EXITING...")
        print("[ROBOT] exiting program.")
