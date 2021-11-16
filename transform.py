# python_str = "AA130003000000000300104E0E07014D6BC57A"
python_str = "AA:1a:00:03:00:00:00:00:04:00:78:2E:0E:00:C8:00:64:00:00:00:01:14:30:F9:DB:52"

python_str = python_str.replace(":", "")

python_str = python_str.lower()

print(python_str)

cpp_str = "{ "

while (python_str != ""):
	byte = python_str[:2]

	hex_byte = "0x" + byte;

	cpp_str = cpp_str + hex_byte + ", "

	python_str = python_str[2:]

cpp_str = cpp_str[: -2]

cpp_str = cpp_str + " }"

print(cpp_str)


