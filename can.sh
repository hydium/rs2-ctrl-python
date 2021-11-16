sudo slcand -o -c -s8 /dev/ttyACM* can0 #assuming only 1 ttyACM* device is connected
sudo ifconfig can0 up
sudo ifconfig can0 txqueuelen 1000