from cmd_combine import *

import struct

import time

import os
import math
import socket

import queue
import threading


# import can

id = "223"

pos_lock = threading.Lock()
wheel_lock = threading.Lock()

event = threading.Event()

#initialize these cmd and put True?
pos_changed = False
pos_cmd = ""

wheel_changed = False
wheel_cmd = ""


# bus = can.interface.Bus(bustype='socketcan', channel='can0', bitrate=1000000)

def prepare_socket(port):
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	except socket.error as err:
		print ("socket creation failed with error %s" %(err))

	s.bind(('', port))

	return s





def send(cmd):
	cmd = cmd.replace(":", "")

	while (cmd != ""):

		end = min(len(cmd), 16)
		to_send = cmd[:end]

		os.system("cansend can0 " + id + "#" + to_send)

		cmd = cmd[end:]




def pos_ctrl():
	global pos_changed
	global event
	global pos_cmd

	socket = prepare_socket(10002)
	last_seq_num = 0

	while True:
		ctrl_byte=0x01
		time_for_action=0x01

		packet = socket.recv(16)

		[seq_num, roll, pitch, yaw] = struct.unpack("<I3f", packet)

		if seq_num < last_seq_num:
			continue

		last_seq_num = seq_num

		roll = (int) (roll * 180 * 10 / math.pi) 
		pitch = (int) (pitch * 180 * 10 / math.pi) 
		yaw = (int) (-yaw * 180 * 10 / math.pi)

		if roll > 300:
			roll = 300

		if roll < -300:
			roll = -300

		if pitch > 1460:
			pitch = 1460

		if pitch < -560:
			pitch = -560



		hex_data = struct.pack('<3h2B', yaw, roll, pitch, ctrl_byte, time_for_action)
		pack_data = ['{:02X}'.format(i) for i in hex_data]
		cmd_data = ':'.join(pack_data)

		cmd = combine(cmd_type='03', cmd_set='0E', cmd_id='00', data=cmd_data)


		pos_lock.acquire()

		pos_changed = True
		pos_cmd = cmd

		pos_lock.release()

		event.set()
		


	

#right controller, wanna switch to left later 
def wheel_ctrl():
	global wheel_changed
	global event
	global wheel_cmd


	socket = prepare_socket(10004)

	last_seq_num = 0

	wheel_position = 2025

	while True:
		packet = socket.recv(22)

		#we only need joystick_y
		[seq_num, joystick_x, joystick_y, index_trigger, grip_trigger, x, y] = struct.unpack("<I4f2?", packet)

		if seq_num < last_seq_num:
			continue

		last_seq_num = seq_num

		if joystick_y > 0.5:
			wheel_position = wheel_position + 45

			if wheel_position > 4095:
				wheel_position = 4095

		elif joystick_y < -0.5:
			wheel_position = wheel_position - 45

			if wheel_position < 0:
				wheel_position = 0

		else:
			continue


		cmd_sub_id = 0x01
		ctrl_type = 0x00
		data_length = 0x02

		hex_data = struct.pack('<3BH', cmd_sub_id, ctrl_type, data_length, wheel_position)
		pack_data = ['{:02X}'.format(i) for i in hex_data]
		cmd_data = ':'.join(pack_data)

		cmd = combine(cmd_type='00', cmd_set='0E', cmd_id='12', data=cmd_data)

		wheel_lock.acquire()

		wheel_changed = True
		wheel_cmd = cmd
		
		wheel_lock.release()

		event.set()
		




if __name__ == '__main__':
	


	# not sure if this is required, but they always send this in the dji demo
	push_cmd = combine(cmd_type='03', cmd_set='0E', cmd_id='07', data='01')
	send(push_cmd)




	pos_thread = threading.Thread(target = pos_ctrl, args = ())
	wheel_thread = threading.Thread(target = wheel_ctrl, args = ())
	# recv_thread = threading.Thread(target = recv_pos, args = ())

	# pos_thread.setDaemon(True)
	# wheel_thread.setDaemon(True)

	pos_thread.start()
	wheel_thread.start()


	
	yaw_speed = 100 * 10
	roll_speed = 100 * 10
	pitch_speed = 100 * 10

	ctrl_byte = 0x80

	hex_data = struct.pack("<3hB", yaw_speed, roll_speed, pitch_speed, ctrl_byte)
	pack_data = ['{:02X}'.format(i) for i in hex_data]
	cmd_data = ':'.join(pack_data)


	speed_cmd = combine(cmd_type = "03", cmd_set = "0E", cmd_id = "01", data = cmd_data)
	


	# last_speed_update = time.perf_counter()

	while True:
		event.wait()


		pos_lock.acquire()





		if pos_changed:
			# print("pos_changed")

			send(speed_cmd)

			send(pos_cmd)
			pos_changed = False

		pos_lock.release()


		wheel_lock.acquire()

		if wheel_changed:
			# print("wheel_changed")
			send(wheel_cmd)
			wheel_changed = False

		wheel_lock.release()


		event.clear()



