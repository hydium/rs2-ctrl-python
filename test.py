from cmd_combine import *
import os

import numpy as np

from ctypes import *

import struct


if __name__ == '__main__':
	np.set_printoptions(formatter={'int':hex})

	test = CDLL('socketcan_python.so')
	
	# test.receive.argtypes = [c_char_p, POINTER(c_int)]

	test.init()

	ctrl_byte=0x01
	time_for_action=0x14

	roll = 0
	pitch = 0
	yaw = - 20 * 10


	hex_data = struct.pack('<3h2B', yaw, roll, pitch, ctrl_byte, time_for_action)
	pack_data = ['{:02X}'.format(i) for i in hex_data]
	cmd_data = ':'.join(pack_data)

	cmd = combine(cmd_type='03', cmd_set='0E', cmd_id='00', data=cmd_data)

	

	cmd = cmd.replace(":", "")

	length = c_int((int) (len(cmd) / 2))

	print(length)

	# start = 0
	# end = min(len(cmd), 16)

	# print(cmd[start:end])

	# while end != len(cmd):
	# 	start = start + 16
	# 	end = end + 16

	# 	end = min(end, len(cmd))

	# 	print(cmd[start:end])


	cmd = cmd.encode('utf-8')

	print(length)

	# print(cmd)

	# s_buf = create_string_buffer(cmd)

	test.transmit.argtypes = [c_char_p, c_int]

	# test.transmit(c_char_p(cmd), length)


	s_buf = create_string_buffer(16)

	# data = bytearray(8)
	length = c_int(0)

	# print(length)

	# test.receive(s_buf, byref(length))
	test.receive(s_buf, byref(length))

	print(s_buf.value)
	print(length.value)


	test.receive(s_buf, byref(length))

	print(s_buf.value)
	print(length.value)

	test.receive(s_buf, byref(length))

	print(s_buf.value)

	# print(type(s_buf.value))

	string = s_buf.value.hex()

	v = s_buf.value

	print(type(repr(v)))

	print(repr(v)[2:-1])

	print(type(s_buf.value))

	print(len(s_buf.value))

	print(string)

	print(length.value)
