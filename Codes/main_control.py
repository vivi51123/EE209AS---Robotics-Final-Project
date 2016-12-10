

########################### Main Control ###########################

import cv2
import numpy as np
import RPi.GPIO as GPIO
import time
import picamera
import math

THRESHOLD = 20
SIZE = 1080

# This function reads in the step number and rotate the motor
# 512 steps --> 360 degree
# 1   step  --> 0.7 degree
def motor(steps):
	# PINS SETUP
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

	if steps < 0: #CW
		for i in range(-steps):
			for step in range(4):
				for pin in range(4):
					GPIO.output(motor_pins[pin], seq_cw[step][pin])
				time.sleep(0.005)
	else: #CCW
		for i in range(steps):
			for step in range(4):
				for pin in range(4):
					GPIO.output(motor_pins[pin], seq_ccw[step][pin])
				time.sleep(0.005)

	GPIO.cleanup()


####### Naive Detection method: determine the width of the light-sheet #######
def naive_detection(img):
	height = len(img[:,0])
	width = len(img[0,:])

	count = 0
	first_sum = 0
	last_sum = 0

	#In order to relieve the computation load of RaspberryPi, sampled at each 10 pixels
	for y in range(0,width,10):
		DETECTED_FLAG = False
		first = 0
		last = 0
		for x in range(0,height):
			if(img[x,y] > THRESHOLD):
				if(not DETECTED_FLAG):
					count += 1
					first = x
					DETECTED_FLAG = True
				else:
					last = x
		first_sum += first
		last_sum += last

	first_sum_ave = first_sum/count
	last_sum_ave = last_sum/count
	d = last_sum_ave - first_sum_ave

	return d
##############################################################################



####### Fine Detection method: determine the width at the center of light-sheet #######
def fine_dection(img):

	SIZE = len(img[:,0])

	up_arr = [0] * SIZE
	down_arr = [0] * SIZE

	print("   - first step analysis ...")

	for y in range(SIZE):
		[up_arr[y], down_arr[y]] = strip_analysis(img[:, y])



	#####
	print("   - find mean square line for upper and lower data points...")

	sum_1 = 0
	sum_x = 0
	sum_y = 0
	sum_xy = 0
	sum_y_2 = 0

	for y in range(SIZE):
		x = up_arr[y]
		if(x!=0):
			sum_1 = sum_1 +1
			sum_x = sum_x + x
			sum_y = sum_y + y
			sum_xy = sum_xy + x*y
			sum_y_2 = sum_y_2 + y*y


	a_up = float(sum_1*sum_xy - sum_x * sum_y) / (sum_1 * sum_y_2 - sum_y*sum_y)
	b_up = float(sum_x - a_up*sum_y) / sum_1
	y_up_avg = float(sum_y) / sum_1




	sum_1 = 0
	sum_y = 0

	for y in range(SIZE):
		x = up_arr[y]
		if(x!=0):
			if(x > a_up*y + b_up):
				sum_1 = sum_1 + 1
				sum_y = sum_y + y


	up_mid_y = float(sum_y) / sum_1
	up_mid_x = up_mid_y * a_up + b_up




	sum_1 = 0
	sum_x = 0
	sum_y = 0
	sum_xy = 0
	sum_y_2 = 0

	for y in range(SIZE):
		x = down_arr[y]
		if(x!=0):
			sum_1 = sum_1 +1
			sum_x = sum_x + x
			sum_y = sum_y + y
			sum_xy = sum_xy + x*y
			sum_y_2 = sum_y_2 + y*y


	a_down = float(sum_1*sum_xy - sum_x * sum_y) / (sum_1 * sum_y_2 - sum_y*sum_y)
	b_down = float(sum_x - a_down*sum_y) / sum_1
	y_down_avg = float(sum_y) / sum_1



	sum_1 = 0
	sum_y = 0

	for y in range(SIZE):
		x = down_arr[y]
		if(x!=0):
			if(x < a_down*y + b_down):
				sum_1 = sum_1 + 1
				sum_y = sum_y + y


	down_mid_y = float(sum_y) / sum_1
	down_mid_x = down_mid_y * a_down + b_down



	mid_y = int(0.5*(up_mid_y + down_mid_y))
	mid_x = int(0.5*(up_mid_x + down_mid_x))



	#####
	print("   - find perpendicular line ...")

	a = 0.5 * (a_up + a_down)
	b = mid_x - mid_y * a
	a_perp = (-1) / a
	b_perp = mid_x - mid_y * a_perp

	sum_of_width_around_mid_y = sum(down_arr[mid_y-2: mid_y+3])-sum(up_arr[mid_y-2: mid_y+3])
	output_width = math.sqrt(1+a_perp*a_perp)*sum_of_width_around_mid_y/(5*a_perp)	


	return output_width
#######################################################################################



###### input is the gray scale of array with size SIZE ######
def strip_analysis(img_array):
	first = 0
	last = 0

	DETECTED_FLAG = False

	for x in range(SIZE):
		if(img_array[x] > THRESHOLD):
			if(not DETECTED_FLAG):
				first = x
				DETECTED_FLAG = True

			else:
				last = x

	return [first, last]
##################################################################




# Setup the picamera
camera = picamera.PiCamera()
camera.resolution = (1080, 1080)
camera.framerate = 10
camera.shutter_speed = 25000000
camera.iso = 600
camera.start_preview()

# Analyze the initial condition of the image
time.sleep(2)
camera.capture('sample.jpg')
img_start = cv2.imread("sample.jpg",0)
d = naive_detection(img_start)
print d

found = False

steps_1 = -100
steps_2 = -50

d_pre = 1080

# Main start without jump and assume initial condition is blurry
while(not found):
	
	if (d > 150):
		motor(steps_1)
		time.sleep(2)
		camera.capture('sample.jpg')
		img = cv2.imread("sample.jpg",0)
		d = naive_detection(img)

		print('naive ' + str(d))

	else:
		if (d_pre-d < 0):
			found = True
		else:
			d_pre = d
			motor(steps_2)
			time.sleep(2)
			camera.capture('sample.jpg')
			img = cv2.imread("sample.jpg",0)
			d = -fine_dection(img)

			print('fine ' + str(d))

time.sleep(5)

#camera.stop_preview()
