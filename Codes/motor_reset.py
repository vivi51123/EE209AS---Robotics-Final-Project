import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)

motor_pins = [11,13,15,16]

for pin in motor_pins:
	GPIO.setup(pin,GPIO.OUT)
	GPIO.output(pin,0)

seq_cw = [[1,0,0,0],
		[0,1,0,0],
		[0,0,1,0],
		[0,0,0,1]]

seq_ccw = [[0,0,0,1],
		[0,0,1,0],
		[0,1,0,0],
		[1,0,0,0]]


# 512 steps --> 360 degree
# 1   step  --> 0.69 degree
# 1000 steps --> one relolution of microscopt --> 0.25 translation height

# 64 nm/step
# negative steps --> downward

steps = 500

if steps < 0:
	for i in range(-steps):
		for step in range(4):
			for pin in range(4):
				GPIO.output(motor_pins[pin], seq_cw[step][pin])
			time.sleep(0.005)
else:
	for i in range(steps):
		for step in range(4):
			for pin in range(4):
				GPIO.output(motor_pins[pin], seq_ccw[step][pin])
			time.sleep(0.005)

GPIO.cleanup()
