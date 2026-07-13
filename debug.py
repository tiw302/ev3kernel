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
* debug module & menu system:                                        [ENGLISH]
    used for testing sensors and checking hardware before a match.
    features an ev3 button menu to select the operating mode without restarting.
    
    [center button] = debug sensors (read reflection values)
    [down button]   = calibrate sensors (run calibration sequence)
    [left button]   = system & battery check
    [up button]     = exit current mode or exit debug loop

.___________________________________________________________________________________________.

* ระบบตรวจสอบและตั้งค่าก่อนแข่ง:                                           [THAI]
    ใช้สำหรับเทสเซ็นเซอร์และเช็คระบบฮาร์ดแวร์ก่อนลงสนามจริง
    มีระบบเมนูให้กดปุ่มบน EV3 เพื่อเลือกโหมดทำงานได้ทันที
    
    [ปุ่มกลาง] = อ่านค่าแสงจากเซ็นเซอร์ (debug sensors)
    [ปุ่มล่าง]  = เข้าโหมดคาลิเบรต (calibrate sensors)
    [ปุ่มซ้าย]  = เช็คระบบและแบตเตอรี่ (system check)
    [ปุ่มบน]   = ออกจากโหมดปัจจุบัน หรือออกจากเมนู
"""

import gc
from pybricks.parameters import Button
from pybricks.tools import wait, StopWatch
from main import Robot

#  ____  _____ ____  _   _  ____ 
# |  _ \| ____| __ )| | | |/ ___|
# | | | |  _| |  _ \| | | | |  _ 
# | |_| | |___| |_) | |_| | |_| |
# |____/|_____|____/ \___/ \____|
#
# >> debug and menu execution
if __name__ == "__main__":
    robot = Robot()
    robot.hub.speaker.beep(1047, 200)
    
    def draw_menu():
        robot.hub.screen.clear()
        robot.hub.screen.print("=== DEBUG MENU ==")
        robot.hub.screen.print("[CEN] Sensors")
        robot.hub.screen.print("[DWN] Calibrate")
        robot.hub.screen.print("[LFT] System")
        robot.hub.screen.print("[UP]  Exit")
        
        print("\n" + "="*40)
        print("      ROBOT SENSOR DEBUG MODE")
        print("="*40)
        print("[CENTER] debug sensors")
        print("[DOWN]   calibrate sensors")
        print("[LEFT]   system & battery check")
        print("[UP]     exit debug menu")
        print("waiting for ev3 button input...")
        print("="*40 + "\n")

    draw_menu()
    
    while True:
        pressed = robot.hub.buttons.pressed()
        
        #  ██████  ███████ ███    ██ ███████  ██████  ██████  ███████ 
        # ██       ██      ████   ██ ██      ██    ██ ██   ██ ██      
        #  █████   █████   ██ ██  ██ ███████ ██    ██ ██████  ███████ 
        #      ██  ██      ██  ██ ██      ██ ██    ██ ██   ██      ██ 
        # ██████   ███████ ██   ████ ███████  ██████  ██   ██ ███████ 
        
        #  ___ ___ _  _ ___  ___  ___   _____ ___ ___ _____
        # / __| __| \| / __/  _ \| _ \ |_   _| __/ __|_   _|
        # \__ \ _|| .` \__ \ (_) |   /   | | | _|\__ \ | |
        # |___/___|_|\_|___/\___/|_|_\   |_| |___|___/ |_|
        #
        # >> mode 1: debug sensors (center button)
        if Button.CENTER in pressed:
            robot.hub.speaker.beep(1319, 200)
            robot.hub.screen.clear()
            robot.hub.screen.print("DEBUG MODE...")
            print("[ROBOT] mode: debug sensors (600s)")
            print("[ROBOT] press [UP] on EV3 to exit.")
            
            # debounce: wait for center to be released
            while Button.CENTER in robot.hub.buttons.pressed():
                wait(10)
            
            watch = StopWatch()
            while watch.time() < 600 * 1000:
                # >> check exit button FIRST before any wait
                if Button.UP in robot.hub.buttons.pressed():
                    print("[ROBOT] exiting debug mode.")
                    break
                
                s1, s2, s3, s4 = [s.reflection() for s in (robot.sensor_1, robot.sensor_2, robot.sensor_3, robot.sensor_4)]
                
                print(f"[ROBOT] S1:{s1:3} | S2:{s2:3} | S3:{s3:3} | S4:{s4:3}")
                
                robot.hub.screen.clear()
                robot.hub.screen.print("= SENSOR VALS =")
                robot.hub.screen.print(f"S1 (L2): {s1}")
                robot.hub.screen.print(f"S2 (L1): {s2}")
                robot.hub.screen.print(f"S3 (R1): {s3}")
                robot.hub.screen.print(f"S4 (R2): {s4}")
                robot.hub.screen.print("[UP] Exit")
                
                wait(100)
            
            robot.hub.speaker.beep(800, 200)
            # redraw menu after mode finishes
            draw_menu()
            # debounce: wait for up to be released AFTER beep
            while Button.UP in robot.hub.buttons.pressed():
                wait(10)
        
        #   ___   _   _    ___ ___ ___    _ _____ ___
        #  / __| /_\ | |  |_ _| _ ) _ \  /_\_   _| __|
        # | (__ / _ \| |__ | || _ \   / / _ \| | | _|
        #  \___/_/ \_\____|___|___/_|_\/_/ \_\_| |___|
        #
        # >> mode 2: calibrate sensors (down button)
        elif Button.DOWN in pressed:
            robot.hub.speaker.beep(1319, 200)
            robot.hub.screen.clear()
            robot.hub.screen.print("CALIBRATING...")
            
            print("[ROBOT] Start: Calibrating (4s)...")
            # debounce: wait for down to be released
            while Button.DOWN in robot.hub.buttons.pressed():
                wait(10)
                
            robot.hub.speaker.beep(500, 200)
            watch = StopWatch()
            mn, mx = 100, 0
            sensors = [robot.sensor_1, robot.sensor_2, robot.sensor_3, robot.sensor_4]
            
            while watch.time() < 4 * 1000:
                for s in sensors:
                    v = s.reflection()
                    if v < mn: mn = v
                    if v > mx: mx = v
                wait(20)
                
            robot.hub.speaker.beep(800, 200)
            print("[ROBOT] Done: Calibrating")
            
            # show result on ev3 screen
            robot.hub.screen.clear()
            robot.hub.screen.print("= CALIBRATED =")
            robot.hub.screen.print(f"BLACK: {mn}")
            robot.hub.screen.print(f"WHITE: {mx}")
            robot.hub.screen.print("Update main.py!")
            
            # print reminder to console
            print("\n" + "="*40)
            print(f">>> BLACK_RAW = {mn}")
            print(f">>> WHITE_RAW = {mx}")
            print("please update BLACK_RAW and WHITE_RAW")
            print("in main.py with the values above.")
            print("="*40 + "\n")
            
            wait(4000)
            
            # redraw menu after mode finishes
            draw_menu()
        
        #  ███████ ██    ██ ███████ ████████ ███████ ███    ███ 
        # ██        ██  ██  ██         ██    ██      ████  ████ 
        # ███████    ████   ███████    ██    █████   ██ ████ ██ 
        #      ██     ██         ██    ██    ██      ██  ██  ██ 
        # ███████     ██    ███████    ██    ███████ ██      ██ 
        
        #  ___ _   _ ___ _____ ___ __  __   ___ _  _ ___ ___
        # / __| | | / __|_   _| __|  \/  | |_ _| \| | __/ _ \
        # \__ \ |_| \__ \ | | | _|| |\/| |  | || .` | _| (_) |
        # |___/\__, |___/ |_| |___|_|  |_| |___|_|\_|_| \___/
        #      |___/
        #
        # >> mode 3: system check (left button)
        elif Button.LEFT in pressed:
            robot.hub.speaker.beep(1047, 200)
            # debounce: wait for left to be released
            while Button.LEFT in robot.hub.buttons.pressed():
                wait(10)
                
            print("[ROBOT] mode: system check (press [UP] to exit)")
            while True:
                # heck exit button FIRST before reading sensors
                if Button.UP in robot.hub.buttons.pressed():
                    robot.hub.speaker.beep(800, 200)
                    break
                
                volts = robot.hub.battery.voltage() / 1000.0
                amps = robot.hub.battery.current() / 1000.0
                percent = (volts - 7.0) / (8.2 - 7.0) * 100
                if percent < 0: percent = 0
                if percent > 100: percent = 100
                
                # get raw ram allocation via garbage collector
                free_kb = gc.mem_free() / 1024.0
                alloc_kb = gc.mem_alloc() / 1024.0
                
                robot.hub.screen.clear()
                robot.hub.screen.print("= SYS CHECK =")
                robot.hub.screen.print(f"BAT: {volts:.2f}V {percent:.0f}%")
                robot.hub.screen.print(f"CUR: {amps:.2f}A")
                robot.hub.screen.print(f"RAM: {free_kb:.0f}KB Free")
                robot.hub.screen.print("[UP] Exit")
                
                # print to console so user can see it on computer screen too
                print(f"[ROBOT] BAT: {volts:.2f}V {percent:.0f}% | CUR: {amps:.2f}A | RAM: {free_kb:.0f}KB Free")
                
                wait(500)
                
            # redraw menu after mode finishes
            draw_menu()
            # debounce: wait for up to be released AFTER beep
            while Button.UP in robot.hub.buttons.pressed():
                wait(10)
        
        # ███████ ██   ██ ██ ████████ 
        # ██       ██ ██  ██    ██    
        # █████     ███   ██    ██    
        # ██       ██ ██  ██    ██    
        # ███████ ██   ██ ██    ██    
        
        # >> mode 4: exit (up button in main menu)
        elif Button.UP in pressed:
            robot.hub.speaker.beep(800, 200)
            robot.hub.screen.clear()
            robot.hub.screen.print("EXITING...")
            print("[ROBOT] exiting debug menu.")
            wait(500)
            break
        
        wait(10)
