gcc -shared -o socketcan_python.so -fPIC socketcan_python.c
# gcc -shared -o socketcan_python.so -fPIC socketcan_python.cpp
# gcc -shared -Wl,-soname,socketcan_python -o socketcan_python.so -fPIC socketcan_python.c