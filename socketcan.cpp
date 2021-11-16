#include <linux/can.h>
#include <linux/can/raw.h>

#include <sys/types.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netinet/in.h>

#include <sys/ioctl.h>
#include <net/if.h>

#include <string.h>

#include <iostream>

#include <vector>
#include <unistd.h>

// #include <sys/syscall.h>
using namespace std;

int sock_fd;
struct sockaddr_can addr;


void transmit(vector<uint8_t> &payload, struct sockaddr_can &addr)
{
	int payload_index = 0;

	while (payload_index < payload.size())
	{
		struct can_frame frame;

		memset(&frame, 0, sizeof(frame));

		uint8_t len = min((uint8_t) payload.size() - payload_index, 8);

		frame.can_id = 0x223;
		frame.can_dlc = len;

		cout << (int) len << endl;

		for (int i = 0; i < len; i++)
		{
			frame.data[i] = payload[payload_index++];
		}

		int nbytes = sendto(sock_fd, (const char *) &frame, sizeof(frame),
                0, (struct sockaddr*)&addr, sizeof(addr));

		// sleep(1);

		cout << nbytes << endl << endl;
	}
}

int main()
{	
	struct ifreq ifr;

	sock_fd = socket(PF_CAN, SOCK_RAW, CAN_RAW);

	// ifr.ifr_ifindex = addr.can_ifindex;

	strcpy(ifr.ifr_name, "can0" );
	
	ioctl(sock_fd, SIOCGIFINDEX, &ifr);

	cout << sizeof(ifr) << endl;
	cout << ifr.ifr_name << endl;

	

	addr.can_family = AF_CAN;
	addr.can_ifindex = ifr.ifr_ifindex;
	// addr.can_ifindex = 0;

	cout << ifr.ifr_ifindex << endl;

	bind(sock_fd, (struct sockaddr *)&addr, sizeof(addr));


	// uint16_t data[] = { 0xaa, 0x13, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x10, 0x4e, 0x0e, 0x07, 0x01, 0x4d, 0x6b, 0xc5, 0x7a };

	vector<uint8_t> payload { 0xaa, 0x13, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 
			0x03, 0x00, 0x10, 0x4e, 0x0e, 0x07, 0x01, 0x4d, 0x6b, 0xc5, 0x7a };

	
	// transmit(payload, addr);

	struct can_frame recv_frame;

	socklen_t addr_len;

	// return 0;

	payload = vector<uint8_t> { 0xaa, 0x1a, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x04, 0x00, 0x78, 0x2e, 
					0x0e, 0x00, 0xc8, 0x00, 0x64, 0x00, 0x00, 0x00, 0x01, 0x14, 0x30, 0xf9, 0xdb, 0x52 };
					

	transmit(payload, addr);


	int nbytes = recvfrom(sock_fd, &recv_frame, sizeof(struct can_frame),
                  0, (struct sockaddr*)&addr, &addr_len);

	if (nbytes > 0)
		cout << "received" << endl;		

	return 0;
}