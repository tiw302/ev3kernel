# EV3Kernel - API Reference

คู่มือรวบรวม API สำหรับการเขียน Mission Scripts พร้อมตัวอย่างการใช้งาน

---

## 1. KINEMATICS & ODOMETRY (เดินกับวัดระยะ)

<details>
<summary><b>[+] <code>move_straight(distance_cm, max_speed=50)</code></b></summary>

![move_straight](../assets/move_straight.png)

สั่งหุ่นยนต์วิ่งตรงหรือถอยหลังตามระยะทาง ควบคุมด้วย Closed-loop PID เพื่อล็อกให้ล้อซ้าย-ขวาหมุนเท่ากันตลอดเวลา ป้องกันหุ่นวิ่งเอียง

**Parameters:**
- `distance_cm` (float): ระยะทางที่ต้องการ (ซม.) บวก=เดินหน้า, ลบ=ถอยหลัง
- `max_speed` (int): ความเร็วสูงสุด (0-100%)

**Example:**
```python
# เดินหน้า 50 ซม. ความเร็ว 60%
robot.move_straight(50, max_speed=60)

# ถอยหลัง 20 ซม. ความเร็ว 40%
robot.move_straight(-20, max_speed=40)
```
</details>

<details>
<summary><b>[+] <code>turn(angle_deg, max_speed=40)</code></b></summary>

![turn](../assets/turn.png)

เลี้ยวอยู่กับที่ (Point turn) ล้อซ้ายและขวาหมุนสวนทางกัน ควบคุมด้วย PID เพื่อให้องศาการเลี้ยวแม่นยำที่สุด

**Parameters:**
- `angle_deg` (float): องศาเป้าหมาย (บวก=เลี้ยวขวา, ลบ=เลี้ยวซ้าย)
- `max_speed` (int): ความเร็วสูงสุดในการหมุน (0-100%)

**Example:**
```python
# หมุนตัวขวา 90 องศา
robot.turn(90, max_speed=40)

# หมุนตัวซ้าย 45 องศา
robot.turn(-45, max_speed=30)
```
</details>

<details>
<summary><b>[+] <code>pivot_turn(angle_deg, pivot_side, max_speed=40)</code></b></summary>

![pivot_turn](../assets/pivot_turn.png)

เลี้ยวแบบตีวง (Pivot turn) โดยล็อกล้อข้างหนึ่งให้อยู่กับที่ และใช้ล้ออีกข้างกวาดเพื่อเลี้ยว

**Parameters:**
- `angle_deg` (float): องศาเป้าหมาย (บวก=หน้าขวา/หลังซ้าย, ลบ=หน้าซ้าย/หลังขวา)
- `pivot_side` (str): เลือกล้อจุดหมุน (`'left'` หรือ `'right'`)
- `max_speed` (int): ความเร็วสูงสุด (0-100%)

**Example:**
```python
# ล็อกล้อขวา, ล้อซ้ายเดินหน้ากวาดไปทางขวา 90 องศา
robot.pivot_turn(90, pivot_side='right', max_speed=40)

# ล็อกล้อซ้าย, ล้อขวาถอยหลังกวาดไปทางซ้าย 45 องศา
robot.pivot_turn(-45, pivot_side='left', max_speed=30)
```
</details>

---

## 2. ALIGNMENT & HOMING (ระบบเทียบเส้น, จัดระเบียบ)

<details>
<summary><b>[+] <code>align_wall(power=-50, time_sec=1.5)</code></b></summary>

![align_wall](../assets/align_wall.png)

วิ่งถอยชนกำแพงเพื่อตั้งลำให้ขนาน มีการหรี่กระแสไฟ (PWM Limit) เพื่อป้องกันเฟืองมอเตอร์แตกเมื่อเกิด Stall

**Parameters:**
- `power` (int): เปอร์เซ็นต์แรงดันไฟที่ใช้ดัน (บวก=หน้า, ลบ=หลัง) แนะนำค่าติดลบ
- `time_sec` (float): ระยะเวลาที่ใช้ดันกำแพง (วินาที)

**Example:**
```python
# ถอยหลังชนกำแพงเพื่อจัดทรง เป็นเวลา 1.5 วินาที
robot.align_wall(power=-50, time_sec=1.5)
```
</details>

<details>
<summary><b>[+] <code>align_line(speed=30, target_val=15, kp=1.0, time_sec=1.0, hold=True)</code></b></summary>

![align_line](../assets/align_line.png)

เทียบเส้นขวางด้วยเซนเซอร์คู่แบบ **3-Step Squaring (มาตรฐานแข่งขัน)**:
1. เดินหน้าเข้าหาเส้นด้วยความเร็ว `speed`
2. ล้อข้างที่เหยียบเส้นก่อนจะหยุดรอ จนกว่าล้ออีกข้างจะเหยียบตาม
3. เปิดระบบ PID ท้ายสุดเพื่อรักษาสมดุลเส้นอย่างสมบูรณ์แบบ

**Parameters:**
- `speed` (int): ความเร็วที่ใช้เดินหน้าหาเส้น (ถ้าหุ่นอยู่บนเส้นอยู่แล้ว ปรับเป็น 0)
- `target_val` (int): ค่าแสงเป้าหมาย (Edge threshold)
- `kp` (float): ค่าแรงดึงกลับของระบบเทียบเส้น
- `time_sec` (float): เวลา Timeout สูงสุดที่ยอมให้เทียบเส้น PID (วินาที)
- `hold` (bool): เปิดล็อกมอเตอร์ค้างไว้เมื่อเทียบเสร็จ
- `left_sensor` (str): พอร์ตเซนเซอร์ซ้าย (ค่าเริ่มต้น "2")
- `right_sensor` (str): พอร์ตเซนเซอร์ขวา (ค่าเริ่มต้น "3")

**Example:**
```python
# เดินหน้าหาเส้นด้วยความเร็ว 30 และสั่งเทียบเส้น 1.0 วินาที
robot.align_line(speed=30, time_sec=1.0)
```
</details>

---

## 3. SENSOR FUSION & LINE TRACKING (ระบบเกาะเส้น 333Hz)

<details>
<summary><b>[+] <code>drive_until_line(speed=40, align=True, left_sensor="2", right_sensor="3")</code></b></summary>

![drive_until_line](../assets/drive_until_line.png)

วิ่งตรงไปเรื่อยๆ จนกว่าเซนเซอร์ทั้ง 2 ตัวจะเหยียบเส้นดำ (ตัดทางแยก)

**Parameters:**
- `speed` (int): ความเร็วในการวิ่ง
- `align` (bool): ควบรวมฟังก์ชัน `align_line()` ให้อัตโนมัติเมื่อเจอเส้น (ถ้าตั้งเป็น True)
- `left_sensor` (str): พอร์ตเซนเซอร์ซ้าย (ค่าเริ่มต้น "2")
- `right_sensor` (str): พอร์ตเซนเซอร์ขวา (ค่าเริ่มต้น "3")

**Example:**
```python
# วิ่งไปหาเส้น พอเจอแล้วจัดทรงเทียบเส้นให้ด้วย
robot.drive_until_line(speed=40, align=True)

# วิ่งหาเส้นโดยใช้คู่เซนเซอร์ 1 และ 4
robot.drive_until_line(speed=40, left_sensor="1", right_sensor="4")
```
</details>

<details>
<summary><b>[+] <code>track_line(speed=None, kp=None, ki=None, kd=None, left_sensor="2", right_sensor="3")</code></b></summary>

![track_line](../assets/track_line.png)

เกาะเส้นดำ (Straddle) ด้วยเซนเซอร์คู่ (ซ้าย-ขวา) ระบบสมการระดับแข่งขันโลก (WRO World-Class Standard):
1. **Sensor Normalization [0.0 - 1.0]:** แปลงค่าแสงเป็นสเกลมาตรฐาน ทำให้ค่า PID `kp/kd` นิ่งเหมือนเดิมแม้เปลี่ยนสนามแข่ง/แสงในห้อง
2. **EMA Low-Pass Filtered Derivative:** กรอง Noise แสงรบกวน ตัดอาการส่ายกระตุกของหุ่น
3. **Quadratic Speed Compensation:** สปีดเต็ม 100% ทางตรง และชะลอเข้าโค้งหักศอกอัตโนมัติ

**Parameters:**
- ดึงค่าตั้งต้น (Default) มาจากดิกชันนารี `TRACK_LINE_CFG` ในไฟล์ `config.py` อัตโนมัติ
- `speed` (int, optional): ความเร็ว (0-100%) - ใส่เพื่อเขียนทับค่าจาก config
- `kp`, `ki`, `kd` (float, optional): ค่าคงที่ PID - ใส่เพื่อเขียนทับค่าจาก config
- `left_sensor` (str): พอร์ตเซนเซอร์ซ้าย (ค่าเริ่มต้น "2")
- `right_sensor` (str): พอร์ตเซนเซอร์ขวา (ค่าเริ่มต้น "3")

**Example:**
```python
# วิ่งตามเส้นด้วยค่าที่ตั้งไว้ใน TRACK_LINE_CFG อัตโนมัติ
robot.track_line()

# เปลี่ยนไปเกาะเส้นด้วยเซนเซอร์พอร์ต 1 และ 2
robot.track_line(left_sensor="1", right_sensor="2")
```
</details>

<details>
<summary><b>[+] <code>track_line_distance(distance_cm, speed=None, kp=None, ki=None, kd=None, left_sensor="2", right_sensor="3")</code></b></summary>

![track_line_distance](../assets/track_line_distance.png)

วิ่งเกาะเส้นควบคู่กับการนับระยะทางด้วย Motor Encoder เมื่อวิ่งครบระยะที่กำหนด หุ่นจะเบรกทันที เหมาะสำหรับเกาะเส้นแค่ช่วงสั้นๆ หรือหนีทางแยก

**Parameters:**
- `distance_cm` (float): ระยะทางที่ต้องการวิ่ง (ซม.)
- ดึงค่าตั้งต้นมาจาก `TRACK_LINE_DISTANCE_CFG` ในไฟล์ `config.py`
- `speed`, `kp`, `ki`, `kd` (optional): ใส่เพื่อเขียนทับค่าจาก config
- `left_sensor` (str): พอร์ตเซนเซอร์ซ้าย (ค่าเริ่มต้น "2")
- `right_sensor` (str): พอร์ตเซนเซอร์ขวา (ค่าเริ่มต้น "3")

**Example:**
```python
# วิ่งตามเส้น 25 ซม. ด้วยค่าจาก TRACK_LINE_DISTANCE_CFG
robot.track_line_distance(25)
```
</details>

<details>
<summary><b>[+] <code>track_line_timer(time_sec, speed=None, kp=None, ki=None, kd=None, left_sensor="2", right_sensor="3")</code></b></summary>

![track_line_timer](../assets/track_line_timer.png)

วิ่งเกาะเส้นโดยจับเวลาแทนระยะทาง มักใช้สั้นๆ เพื่อข้ามผ่านเส้นตัดขวาง

**Parameters:**
- `time_sec` (float): เวลาที่ต้องการวิ่ง (วินาที)
- ดึงค่าตั้งต้นมาจาก `TRACK_LINE_TIMER_CFG` ในไฟล์ `config.py`
- `speed`, `kp`, `ki`, `kd` (optional): ใส่เพื่อเขียนทับค่าจาก config
- `left_sensor` (str): พอร์ตเซนเซอร์ซ้าย (ค่าเริ่มต้น "2")
- `right_sensor` (str): พอร์ตเซนเซอร์ขวา (ค่าเริ่มต้น "3")

**Example:**
```python
# วิ่งตามเส้น 1.2 วินาที ด้วยค่าจาก TRACK_LINE_TIMER_CFG
robot.track_line_timer(1.2)
```
</details>

---

## 4. ACTUATORS / GRIPPERS (ระบบควบคุมแขนกล)

<details>
<summary><b>[+] <code>lift_a(angle, speed=80, power=50, wait=True)</code></b> / <b><code>lift_d(...)</code></b></summary>

![lift](../assets/lift.png)

สั่งแขนกลไปยังองศาที่กำหนด รองรับระบบลิมิตกระแสไฟ (Power Limit) ป้องกันเฟืองมอเตอร์พังเมื่อแขนถูกขัดหรือหนีบของแน่นเกินไป

**Parameters:**
- `angle` (float): องศาเป้าหมาย (Absolute position)
- `speed` (int): ความเร็วในการหมุน (0-100%)
- `power` (int): เปอร์เซ็นต์กระแสไฟสูงสุดที่อนุญาต (Torque limit)
- `wait` (bool): `True` = Blocking รอจนยกเสร็จ, `False` = Async ทำงานเบื้องหลังรหัสบรรทัดถัดไปทันที

**Example:**
```python
# [Blocking] ยกแขน A ไปที่ 90 องศา แล้วรอจนกว่าจะยกเสร็จ
robot.lift_a(90, speed=80, wait=True)

# [Async] สั่งแขน D หุบไปที่ 45 องศา แล้วสั่งรถวิ่งตรงต่อทันทีโดยไม่ต้องรอแขนหุบเสร็จ
robot.lift_d(45, speed=60, wait=False)
robot.move_straight(20)
```
</details>

<details>
<summary><b>[+] <code>reset_lift_a(angle=0)</code> / <code>reset_lift_d(...)</code></b></summary>

เซ็ตค่าองศาปัจจุบันของมอเตอร์แขนกลให้เป็นค่าที่ระบุ (Zeroing/Homing)

**Example:**
```python
# ตอนเริ่มรันโค้ด ให้เซ็ตตำแหน่งปัจจุบันของแขนทั้งสองเป็น 0 องศา
robot.reset_lift_a(0)
robot.reset_lift_d(0)
```
</details>

<details>
<summary><b>[+] <code>release_a()</code> / <code>release_d()</code></b></summary>

สั่งปลดโหลดมอเตอร์ ปล่อยให้เฟืองลื่นไหล (Float) เพื่อพักมอเตอร์และประหยัดแบตเตอรี่

**Example:**
```python
# วางของเสร็จแล้ว ปล่อยแขนลื่นเป็นอิสระ
robot.release_a()
```
</details>

---

## 5. SYSTEM / LOW-LEVEL (ระบบสั่งพื้นฐาน)

<details>
<summary><b>[+] <code>drive(left_speed, right_speed)</code></b></summary>

เจาะทะลุระบบ PID และยิงคำสั่งความเร็วดิบลง Motor Controller โดยตรง เหมาะสำหรับสั่งล้อลุยๆ ที่ไม่ต้องสนความแม่นยำ

**Parameters:**
- `left_speed`, `right_speed` (int): ความเร็วดิบของล้อ (องศา/วินาที)

**Example:**
```python
# สั่งมอเตอร์หมุนดิบๆ ล้อซ้าย 300, ล้อขวา 300 (องศา/วิ)
robot.drive(300, 300)
wait(1000)
robot.stop_drive()
```
</details>

<details>
<summary><b>[+] <code>stop_drive(hold=True)</code></b></summary>

เบรกฉุกเฉินสำหรับล้อตอนเคลื่อนที่
**Parameters:**
- `hold` (bool): `True` = ล็อกล้อแข็ง (Active Hold) กันรถไหล, `False` = เบรกแล้วปล่อยฟรี (Coast)

**Example:**
```python
# เบรกและล็อกล้อแข็ง
robot.stop_drive(hold=True)

# เบรกแล้วปล่อยล้อฟรี (ใช้นิ้วดันรถเข็นได้)
robot.stop_drive(hold=False)
```
</details>
