from cmd_combine import *
import struct

import time

import threading

from ctypes import *

import socket

import binascii

import math



socketcan = CDLL('socketcan_python.so')

target_pos_lock = threading.Lock()
current_pos_lock = threading.Lock()
wheel_lock = threading.Lock()
start_recording_lock = threading.Lock()
stop_recording_lock = threading.Lock()

target_roll = 0
target_pitch = 0
target_yaw = 0

current_roll = 0
current_pitch = 0
current_yaw = 0



wheel_changed = False
wheel_cmd = ""
wheel_length = 0


start_recording = False
stop_recording = False

def prepare_socket(port):
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	except socket.error as err:
		print ("socket creation failed with error %s" %(err))

	s.bind(('', port))

	return s


def target_pos_listen(): #oculus_pos
	global target_roll
	global target_pitch
	global target_yaw

	socket = prepare_socket(10002)
	last_seq_num = 0

	while True:
		packet = socket.recv(16)

		[seq_num, roll, pitch, yaw] = struct.unpack("<I3f", packet)

		if seq_num < last_seq_num:
			continue

		last_seq_num = seq_num

		roll = -roll * 180 / math.pi
		pitch = pitch * 180 / math.pi
		yaw = -yaw * 180 / math.pi


		target_pos_lock.acquire()

		target_roll = roll
		target_pitch = pitch
		target_yaw = yaw

		target_pos_lock.release()



#left controller
def controller_state():
	global wheel_changed
	global event
	global wheel_cmd
	global wheel_length


	socket = prepare_socket(10004)

	last_seq_num = 0

	wheel_position = 2025

	start_recording_pressed = False
	stop_recording_pressed = False

	# start_recording_change = False
	# stop_recording_change = False


	while True:
		packet = socket.recv(22)

		#we only need joystick_y, x, y
		[seq_num, joystick_x, joystick_y, index_trigger, grip_trigger, x, y] = struct.unpack("<I4f2?", packet)

		if seq_num < last_seq_num:
			continue

		last_seq_num = seq_num

		# if x:
		# 	print("X")


		# if x and not start_recording_pressed:
		# 	# start_recording_lock.acquire()
		# 	start_recording = True
		# 	# start_recording_lock.release()

		# 	start_recording_pressed = True
		# elif not x:
		# 	start_recording_pressed = False

		# if y and not stop_recording_pressed:
		# 	# stop_recording_lock.acquire()
		# 	stop_recording = True
		# 	# stop_recording_lock.release()

		# 	stop_recording_pressed = True
		# elif not y:
		# 	stop_recording_pressed = False				


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

		cmd = cmd.replace(":", "")
		cmd = cmd.encode("utf-8")
		length = c_int((int) (len(cmd) / 2))

		wheel_lock.acquire()

		wheel_changed = True
		wheel_cmd = cmd
		wheel_length = length

		wheel_lock.release()






def check_head_crc(head_data):
        cmd_prefix = ":".join(head_data[:10])
        pack_crc = ":".join(head_data[-2:])
        crc = calc_crc(cmd_prefix, 16)
        if crc.upper() == pack_crc.upper():
            return True
        else:
            return False

def check_pack_crc(pack_data):
    cmd_prefix = ":".join(pack_data[:-4])
    pack_crc = ":".join(pack_data[-4:])
    crc = calc_crc(cmd_prefix, 32)
    if crc.upper()  == pack_crc.upper():
        return True
    else:
        return False

def recv_can_frame():
	s_buf = create_string_buffer(16)
	length = c_int(0)

	socketcan.receive(s_buf, byref(length))

	# print(s_buf.value)

	frame_string = s_buf.value.decode("utf-8")[:length.value]

	frame = []

	for i in range(0, len(frame_string), 2):
		frame.append(frame_string[i : i + 2])

	# print()
	return frame

def can_listen():
	global socketcan

	global current_roll
	global current_pitch
	global current_yaw

	#global wheel_position

	print(10)

	while True:
		can_data = recv_can_frame()
		gimbal_packet = [] 
		gimbal_packet_len = 0

		if len(can_data) <= 0:
			continue

		if can_data[0] == "aa":
			gimbal_packet.extend(can_data)
			gimbal_packet_len = int(can_data[1], 16) # not sure about this

			

			if gimbal_packet_len < 14 or gimbal_packet_len > 100: #idk maybe bug on my side
				continue

			
		else:
			continue

		while len(gimbal_packet) < gimbal_packet_len:
			can_data = recv_can_frame()
			gimbal_packet.extend(can_data)


		if gimbal_packet_len != len(gimbal_packet):
			continue

			#fix this later, check head earlier
		# if not (check_head_crc(gimbal_packet) and check_pack_crc(gimbal_packet)):
		# 	continue



		if gimbal_packet[12] == "0e" and gimbal_packet[13] == "02": #position
			if gimbal_packet[14] != "00": #reply code
				continue

			if gimbal_packet[15] != "01": #I think I want attitude angle
				continue

			string_data = "".join(gimbal_packet[16:22])
			hex_data = binascii.a2b_hex(string_data)

			[yaw, roll, pitch] = struct.unpack("<3h", hex_data)


			roll = roll / 10
			pitch = pitch / 10
			yaw = yaw / 10

			#some crazy packet, need to check crc probably
			if roll > 180 or roll < -180 or pitch > 180 or pitch < -180 or roll > 180 or roll < -180:
				continue

			current_pos_lock.acquire()

			current_roll = roll
			current_pitch = pitch
			current_yaw = yaw

			current_pos_lock.release()


def increase_roll_speed(diff):

	if abs(diff) >= 10 and abs(diff) <= 20:
		diff = math.copysign(20, diff)

	if abs(diff) >= 2 and abs(diff) < 10:
		diff = math.copysign(10, diff) + diff

	return diff

def increase_speed(diff):

	if abs(diff) >= 10 and abs(diff) <= 15:
		diff = math.copysign(15, diff)


	if abs(diff) >= 2 and abs(diff) < 10:
		diff = math.copysign(5, diff) + diff

	return diff

if __name__ == '__main__':
	socketcan.init()

	pos_thread = threading.Thread(target = target_pos_listen, args = ())
	controller_thread = threading.Thread(target = controller_state, args = ())
	listen_thread = threading.Thread(target = can_listen, args = ())

	# query wheel pos here maybe gimbal pos too

	pos_thread.start()
	controller_thread.start()
	listen_thread.start()

	hex_data = struct.pack("<H", 0x03)
	pack_data = ['{:02X}'.format(i) for i in hex_data]
	cmd_data = ':'.join(pack_data)

	start_recording_cmd = combine(cmd_type = '00', cmd_set = '0D', cmd_id = "01", data = cmd_data)
	start_recording_cmd = start_recording_cmd.replace(":", "")
	start_recording_cmd = start_recording_cmd.encode("utf-8")
	start_recording_length = c_int((int) (len(start_recording_cmd) / 2))


	hex_data = struct.pack("<H", 0x02)
	pack_data = ['{:02X}'.format(i) for i in hex_data]
	cmd_data = ':'.join(pack_data)

	stop_recording_cmd = combine(cmd_type = '00', cmd_set = '0D', cmd_id = "01", data = cmd_data)
	stop_recording_cmd = stop_recording_cmd.replace(":", "")
	stop_recording_cmd = stop_recording_cmd.encode("utf-8")
	stop_recording_cmd = c_int((int) (len(stop_recording_cmd) / 2))


	


	while True:
		current_pos_lock.acquire()

		current_roll_ = current_roll
		current_pitch_ = current_pitch
		current_yaw_ = current_yaw

		current_pos_lock.release()



		target_pos_lock.acquire()

		target_roll_ = target_roll
		target_pitch_ = target_pitch
		target_yaw_ = target_yaw

		target_pos_lock.release()


		pos_query_cmd = combine(cmd_type = '03', cmd_set = '0E', cmd_id = '02', data = '01')
		pos_query_cmd = pos_query_cmd.replace(":", "")
		pos_query_cmd = pos_query_cmd.encode("utf-8")
		length = c_int((int) (len(pos_query_cmd) / 2))

		socketcan.transmit(c_char_p(pos_query_cmd), length)



		roll_diff = target_roll_ - current_roll_
		pitch_diff = target_pitch_ - current_pitch_
		yaw_diff = target_yaw_ - current_yaw_



		roll_diff = increase_roll_speed(roll_diff)
		pitch_diff = increase_speed(pitch_diff)
		yaw_diff = increase_speed(yaw_diff)

		


		while yaw_diff >= 180:
			yaw_diff = yaw_diff - 360

		while yaw_diff <= -180:
			yaw_diff = yaw_diff + 360


		# if roll_diff > 60 or roll_diff < -60 or pitch_diff > 60 or pitch_diff < -60 or yaw_diff > 90 or yaw_diff < -90:
		# 	print("target")
		# 	print(target_roll_)
		# 	print(target_pitch_)
		# 	print(target_yaw_)


		# 	print("current")
		# 	print(current_roll_)
		# 	print(current_pitch_)
		# 	print(current_yaw_)



		roll_speed = (int) (roll_diff  * 10)
		pitch_speed = (int) (pitch_diff  * 10)
		yaw_speed = (int) (yaw_diff  * 10)



		# roll_speed = 0
		# pitch_speed = 0
		# yaw_speed = 0

		ctrl_byte = 0x80

		hex_data = struct.pack("<3hB", yaw_speed, roll_speed, pitch_speed, ctrl_byte)
		pack_data = ['{:02X}'.format(i) for i in hex_data]
		cmd_data = ':'.join(pack_data)


		speed_cmd = combine(cmd_type = "00", cmd_set = "0E", cmd_id = "01", data = cmd_data)

		speed_cmd = speed_cmd.replace(":", "")
		speed_cmd = speed_cmd.encode("utf-8")
		speed_length = c_int((int) (len(speed_cmd) / 2))


		socketcan.transmit(c_char_p(speed_cmd), speed_length)


		wheel_lock.acquire()

		if wheel_changed:
			wheel_changed = False
			socketcan.transmit(c_char_p(wheel_cmd), wheel_length)


		wheel_lock.release()


		# start_recording_lock.acquire()
		
		if start_recording:
			print("start")
			socketcan.transmit(c_char_p(start_recording_cmd), start_recording_length)
			start_recording = False

		# start_recording_lock.release()


		# stop_recording_lock.acquire()
		
		if stop_recording:
			print("stop")
			socketcan.transmit(c_char_p(stop_recording_cmd), stop_recording_length)
			stop_recording = False

		# stop_recording_lock.release()

		time.sleep(0.01)