#include <linux/can.h>
#include <linux/can/raw.h>

#include <sys/types.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netinet/in.h>

#include <sys/ioctl.h>
#include <net/if.h>

#include <string.h>

#include <stdio.h>

#include <unistd.h>


int sock_fd;
struct sockaddr_can addr;

void init()
{
    struct ifreq ifr;

	sock_fd = socket(PF_CAN, SOCK_RAW, CAN_RAW);

	struct can_filter filter;

	filter.can_id = 0x222; //546 in decimal
	filter.can_mask = CAN_SFF_MASK;

	setsockopt(sock_fd, SOL_CAN_RAW, CAN_RAW_FILTER, &filter, sizeof(filter));



	strcpy(ifr.ifr_name, "can0" );
	
	ioctl(sock_fd, SIOCGIFINDEX, &ifr);
	

	addr.can_family = AF_CAN;
	addr.can_ifindex = ifr.ifr_ifindex;





	bind(sock_fd, (struct sockaddr *)&addr, sizeof(addr));
}



uint8_t ascii_to_int(uint8_t symbol)
{
	if (symbol >= 97) { //caps A-F
		return symbol - 87;
	} else if (symbol >= 65) { //lower case a-f
		return symbol - 55;
	} else {  //0-9 digit
		return symbol - 48;
	}
}


void transmit(char *data, int length)
{
	// vector<uint8_t> payload = vector<uint8_t> { 0xaa, 0x1a, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x04, 0x00, 0x78, 0x2e, 
	// 				0x0e, 0x00, 0xc8, 0x00, 0x64, 0x00, 0x00, 0x00, 0x01, 0x14, 0x30, 0xf9, 0xdb, 0x52 };
	// uint8_t payload[] = { 0xaa, 0x1a, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x04, 0x00, 0x78, 0x2e, 
	// 				0x0e, 0x00, 0xc8, 0x00, 0x64, 0x00, 0x00, 0x00, 0x01, 0x14, 0x30, 0xf9, 0xdb, 0x52 };

	

	uint8_t payload[length]; 

	for (int i = 0; i < length; i++)
	{

		uint8_t first_char = ascii_to_int(data[2 * i]);
		uint8_t second_char = ascii_to_int(data[2 * i + 1]);

		payload[i] = first_char * 16 + second_char;
	}

	

	size_t payload_size = sizeof(payload) / sizeof(uint8_t);

	int payload_index = 0;

	while (payload_index < payload_size)
	{
		struct can_frame frame;

		memset(&frame, 0, sizeof(frame));

		uint8_t len;
		if (payload_size - payload_index > 8)
		{
			len = 8;
		} else {
			len = (uint8_t) payload_size - payload_index;
		}

		frame.can_id = 0x223;
		frame.can_dlc = len;

		for (int i = 0; i < len; i++)
		{
			frame.data[i] = payload[payload_index++];
			// printf("0x%02X ", frame.data[i]);
		}

		// printf("\n");

		int nbytes = sendto(sock_fd, (const char *) &frame, sizeof(frame),
                0, (struct sockaddr*)&addr, sizeof(addr));

	}
}

void receive(char *data, int *length)
{
	struct can_frame frame;

	socklen_t len;

	int nbytes = recvfrom(sock_fd, &frame, sizeof(struct can_frame),
	                  0, (struct sockaddr*)&addr, &len);


	if (nbytes < 0) { //sometimes it comes here but the data in the frame is fine, so I just ignore this for now
        perror("can raw socket read");
        return;
	}

	/* paranoid check ... */
	if (nbytes < sizeof(struct can_frame)) {
        fprintf(stderr, "read: incomplete CAN frame\n");
        return;
	}

	// printf("can id: %x\n", frame.can_id);

	for (int i = 0; i < frame.can_dlc; i++)
	{
		// printf("%02x",frame.data[i]);  
  		sprintf(&data[i*2],"%02x", frame.data[i]); //upper case 
	}

	// printf("\n");


	// memcpy(data, &frame.data, frame.can_dlc);

	*length = frame.can_dlc * 2;
}

