import serial
import time
import os
import serial_comm
from PIL  import Image
import numpy as np

cmd = [0x00]*26 # array to save Command 
rsp = [0x00]*26 # array to save response data of cmd
cmd_p = [] # array to save command data packet
rsp_p = [] # array to save response data packet of cmd_p

Baudrate = {0:9600, 1:19200, 2:38400, 3:57600, 4:115200, 5:230400, 6:460800, 7:921600}
ser_com = serial_comm.get_serial_port()
ser = serial.Serial(
    ser_com,
    baudrate = Baudrate[4],
    timeout = 1
)

Param = {
    'Dev_ID': 0x00, #Device ID; range 1 ~ 255
    'Secu_Level': 0x01, #Security level; range 1 ~ 5
    'Dup_Check': 0x02, # Duplication Check status; 0: enable; 1: disable
    'Baudrate': 0x03, #Baudrate; 0:9600, 1:19200, 2:38400, 3:57600, 4:115200, 5:230400, 6:460800, 7:921600
    'Auto_Learn': 0x04, # Aduo Learn status; 0: enable; 1: disable
}


Image_width = 192 # Image width of fingeprint image 
Image_height = 192 # Image height of fingerprint image

PREFIX_CODE                 = 0xAA55
PREFIX_CODE_P               = 0x5AA5
SOURCE_ID                   = 0x00
DEVICE_ID                   = 0x00

#********************Command List********************#
CMD_TEST_CONNECTION         = 0x0001 # Test device connect status
CMD_SET_PARAM               = 0x0002 # Set Device parameter
CMD_GET_PARAM               = 0x0003 # Get Device parameter
CMD_DEVICE_INFO             = 0x0004 # Read Device information
CMD_GET_IMAGE               = 0x0020 # Get finger image
CMD_FINGER_DETECT           = 0x0021 # Detect finger 
CMD_UP_IMAGE_CODE           = 0x0022 # Upload finger image to host device
CMD_DOWN_IMAGE              = 0x0023 # Download finger image to device
CMD_SLED_CTRL               = 0x0024 # Control sensor LED
CMD_STORE_CHAR              = 0x0040 # Save template data to device database
CMD_LOAD_CHAR               = 0x0041 # Read tempalte from database and save to rambuffer
CMD_UP_CHAR                 = 0x0042 # Upload tempalte to host device from rambuffer
CMD_DOWN_CHAR               = 0x0043 # Download template to rambuffer from host device
CMD_DEL_CHAR                = 0x0044 # Delete fingerprint in range
CMD_GET_EMPTY_ID            = 0x0045 # Get the empty id in range
CMD_GET_STATUS              = 0x0046 # Get enroll status of ID
CMD_GET_BROKEN_ID           = 0x0047 # Get ID of broken template in range
CMD_GET_ENROLL_COUNT        = 0x0048 # Get enroll count in range
CMD_GENERATE                = 0x0060 # Generate template from the image which is aved in imagebuffer
CMD_MERGE                   = 0x0061 # Merge image template and save
CMD_MATCH                   = 0x0062 # Match template in two rambuffer
CMD_SEARCH                  = 0x0063 # Verify in 1:N in range
CMD_VERIFY                  = 0x0064 # Verify template between rambuffer and certian fingerprint in database
CMD_SET_MODULE_SN           = 0x0008 # Set device SN
CMD_GET_MODULE_SN           = 0x0009 # Get device SN
CMD_GET_ENROLLED_ID_LIST    = 0x0049 # Get enrolled ID
CMD_ENMTER_STANDBY_STATE    = 0x000C # Set devoce to sleep
CMD_ADJUST_SENSOR           = 0x0025 # Adjust sensor

#********************Error Code********************#
class ERR_Code:
    def __init__(self):
        self.ERR_SUCCESS                 = 0x00 # Command processed sucessfully
        self.ERR_FAIL                    = 0x01 # Command processed fail
        self.ERR_VERIFY                  = 0x10 # Fail to verify fingerprint in 1:1 mode
        self.ERR_IDENTIFY                = 0x11 # Fingerprint template isn't exist in 1:N mode
        self.ERR_TMPL_EMPTY              = 0x12 # Template isn't exist in the range
        self.ERR_TMPL_NOT_EMPTY          = 0x13 # Template is exist in the range
        self.ERR_ALL_TMPL_EMPTY          = 0x14 # No registered template
        self.ERR_EMPTY_ID_NOEXIST        = 0x15 # No available template ID
        self.ERR_BROKEN_ID_NOEXIST       = 0x16 # No broken template
        self.ERR_INVALID_TMPL_DATA       = 0x17 # The template is invalid
        self.ERR_DUPLICATION_ID          = 0x18 # The ID has registered
        self.ERR_BAD_QUALITY             = 0x19 # Bad image quality
        self.ERR_MERGE_FAIL              = 0x1A # Fail to merge template
        self.ERR_NO_AUTHORIZED           = 0x1B # Do not authorize password
        self.ERR_MEMORY                  = 0x1C # Fail to flashed memory
        self.ERR_INVALID_TMPL_NO         = 0x1D # The template ID is invalid
        self.ERR_INVALID_PARAM           = 0x22 # Use wrong parameter
        self.ERR_GEN_COUNT               = 0x25 # Invalid count to merge
        self.ERR_TIME_OUT                = 0x23 # Fingerpint input timeout
        self.ERR_INVALID_BUFFER_ID       = 0x26 # Wrong buffer ID
        self.ERR_FP_NOT_DETECTED         = 0x28 # Do not detect finger
        self.ERR_FP_CANCEL               = 0x41 # Command is cancel

class CMD_Packet: # Command Packet 26 bytes
    def __init__(self):
        self.Prefix         = PREFIX_CODE   # 2 bytes
        self.SID            = SOURCE_ID     # 1 byte
        self.DID            = DEVICE_ID     # 1 byte
        self.CMD            = 0x0000        # 2 bytes
        self.LEN            = 0x0000        # 2 bytes
        self.Data           = [0x00]*16     # 16 bytes
        self.CKS            = 0x0000        # 2 bytes

class RSP_Packet: # Received Packet 26 bytes
    def __init__(self):
        self.Prefix         = PREFIX_CODE   # 2 bytes
        self.SID            = SOURCE_ID     # 1 byte
        self.DID            = DEVICE_ID     # 1 byte
        self.RCM            = 0x0000        # 2 bytes
        self.LEN            = 0x0000        # 2 bytes
        self.RET            = 0x0000        # 2 bytes
        self.Data           = [0x00]*14     # 14 bytes
        self.CKS            = 0x0000        # 2 bytes

class CMD_DATA_Packet: # Command DATA Packet
    def __init__(self):
        self.Prefix         = PREFIX_CODE   # 2 bytes
        self.SID            = SOURCE_ID     # 1 byte
        self.DID            = DEVICE_ID     # 1 byte
        self.CMD            = 0x0000        # 2 bytes
        self.LEN            = 0x0000        # 2 bytes
        self.Data           = []            # Data packaet, < 500 bytes
        self.CKS            = 0x0000        # 2 bytes

class RSP_DATA_Packet: # Received data Packet
    def __init__(self):
        self.Prefix         = PREFIX_CODE   # 2 bytes
        self.SID            = SOURCE_ID     # 1 byte
        self.DID            = DEVICE_ID     # 1 byte
        self.CMD            = 0x0000        # 2 bytes
        self.LEN            = 0x0000        # 2 bytes
        self.Data           = []            # Data packaet, < 500 bytes
        self.CKS            = 0x0000        # 2 bytes

CMD = CMD_Packet()
RSP = RSP_Packet()
CMD_DATA = CMD_DATA_Packet()
RSP_DATA = RSP_DATA_Packet()
ERR = ERR_Code()

#*********************************************
# Function: Send a common command via serial port
# @param:
#       timeout: Timeout period to receive data packet
# @Return: 
#       None
#*********************************************
def SendCmd(timeout = 3):
    Checksum = 0x00
    global CMD, cmd
    cmd[0] = (CMD.Prefix & 0xFF)         # Low byte of wPrefix
    cmd[1] = (CMD.Prefix >> 8) & 0xFF    # High byte of wPrefix
    cmd[2] = CMD.SID & 0xFF
    cmd[3] = CMD.DID & 0xFF
    cmd[4] = CMD.CMD & 0xFF
    cmd[5] = (CMD.CMD >> 8) & 0xFF
    cmd[6] = CMD.LEN & 0xFF
    cmd[7] = (CMD.LEN>> 8) & 0xFF
    for i in range(16):
        cmd[8 + i] = CMD.Data[i]
    for i in range(24): # Calculate checksum for the first 24 bytes
        Checksum += cmd[i]
    cmd[24] = Checksum & 0xFF             # Low byte of wCheckSum
    cmd[25] = (Checksum >> 8) & 0xFF      # High byte of wCheckSum
    #print("Sending command:", [hex(x) for x in cmd])
    #for i in range(24):
    #    ser.write(cmd[i])
    ser.write(cmd)
    #print(cmd)
    cmd = [0x00] * 26
    CMD = CMD_Packet() #Reset the CMD packet

#*********************************************
# Function: Send image data packet via serial port
# @param:
#       file_path: The path of image data file
#       width: The width of fingerprint image
#       height: The height of fingerprint image
# @Return: None
#*********************************************
def Send_Packet(file_path, width = 192, height = 192):
    Checksum = 0x00
    bar_length = 20 
    global CMD, cmd
    #Read image data from file
    image_data = [] # array to save image data
    try:
        with open(file_path, "r") as f:
            for line in f:
                values = line.strip().split()
                for value in values:
                    image_data.append(int(value, 16))
    except Exception as e:
        print("Error reading image file:", e)
        return ERR.ERR_FAIL
    print(f"Image data length: {len(image_data)}")
    packet_num = int ((width * height) / 496)
    packet_last = int((width * height) % 496)
    for i in range (packet_num):
        CMD_DATA.Prefix = PREFIX_CODE_P
        CMD_DATA.SID = SOURCE_ID
        CMD_DATA.DID = DEVICE_ID
        CMD_DATA.CMD = CMD_DOWN_IMAGE
        CMD_DATA.LEN = 496 + 2
        CMD_DATA.Data = [0x00] * 496
        for j in range (496):
            CMD_DATA.Data[j] = image_data[i*496 + j]
        Checksum = 0x00
        cmd_p = [0x00] * 510
        cmd_p[0] = (CMD_DATA.Prefix & 0xFF)         # Low byte of wPrefix
        cmd_p[1] = (CMD_DATA.Prefix >> 8) & 0xFF    # High byte of wPrefix
        cmd_p[2] = CMD_DATA.SID & 0xFF
        cmd_p[3] = CMD_DATA.DID & 0xFF
        cmd_p[4] = CMD_DATA.CMD & 0xFF
        cmd_p[5] = (CMD_DATA.CMD >> 8) & 0xFF
        cmd_p[6] = CMD_DATA.LEN & 0xFF
        cmd_p[7] = (CMD_DATA.LEN>> 8) & 0xFF
        cmd_p[8] = packet_num & 0xFF          # Packet number
        cmd_p[9] = (packet_num >> 8) & 0xFF   # Packet number high byte
        for k in range(496):
            cmd_p[10 + k] = CMD_DATA.Data[k]
        for k in range(508): # Calculate checksum for the first 508 bytes
            Checksum += cmd_p[k]
        cmd_p[508] = Checksum & 0xFF             # Low byte of wCheckSum
        cmd_p[509] = (Checksum >> 8) & 0xFF      # High byte of wCheckSum
        progress = (i + 1) / (packet_num + (1 if packet_last > 0 else 0))
        filled_length = int(bar_length * progress)
        bar = '#' * filled_length + ' ' * (bar_length - filled_length)
        print(f"Sending data packet [{bar}] {i + 1}/{packet_num+ (1 if packet_last > 0 else 0)} ({progress:.0%})", end='\r', flush=True)
        ser.write(cmd_p)
        Rx_cmd(12)  # Read ACK from device

    if packet_last > 0:
        CMD_DATA.Prefix = PREFIX_CODE_P
        CMD_DATA.SID = SOURCE_ID
        CMD_DATA.DID = DEVICE_ID
        CMD_DATA.CMD = CMD_DOWN_IMAGE
        CMD_DATA.LEN = packet_last + 2
        CMD_DATA.Data = [0x00] * packet_last
        for j in range (packet_last):
            CMD_DATA.Data[j] = image_data[packet_num*496 + j]
        Checksum = 0x00
        cmd_p = [0x00] * (packet_last + 14)
        cmd_p[0] = (CMD_DATA.Prefix & 0xFF)         # Low byte of wPrefix
        cmd_p[1] = (CMD_DATA.Prefix >> 8) & 0xFF    # High byte of wPrefix
        cmd_p[2] = CMD_DATA.SID & 0xFF
        cmd_p[3] = CMD_DATA.DID & 0xFF
        cmd_p[4] = CMD_DATA.CMD & 0xFF
        cmd_p[5] = (CMD_DATA.CMD >> 8) & 0xFF
        cmd_p[6] = CMD_DATA.LEN & 0xFF
        cmd_p[7] = (CMD_DATA.LEN>> 8) & 0xFF
        cmd_p[8] = (packet_num + 1) & 0xFF          # Packet number
        cmd_p[9] = ((packet_num + 1) >> 8) & 0xFF   # Packet number high byte
        for k in range(packet_last):
            cmd_p[10 + k] = CMD_DATA.Data[k]
        for k in range(len(cmd_p) -2): # Calculate checksum for the first bytes
            Checksum += cmd_p[k]
        cmd_p[len(cmd_p) -2] = Checksum & 0xFF             # Low byte of wCheckSum
        cmd_p[len(cmd_p) -1] = (Checksum >> 8) & 0xFF      # High byte of wCheckSum
        print(f"\nAll packets sent successfully!")
        ser.write(cmd_p)
        Rx_cmd(12)
    return ERR.ERR_SUCCESS

#*********************************************
# Function: Process received command packet
# @param:
#       flag: reserved
#       len: length of data packet
# @Return: 
#       None
#*********************************************
def Rx_CMD_Process(flag, len = 26):
    if (len > 26):
        RSP_DATA.Prefix =rsp_p[0] + (rsp_p[1] << 8)
        RSP_DATA.SID = rsp_p[2] & 0xFF
        RSP_DATA.DID = rsp_p[3] & 0xFF
        RSP_DATA.RCM = rsp_p[4] | (rsp_p[5] << 8)
        RSP_DATA.LEN = rsp_p[6] | (rsp_p[7] << 8)
        RSP_DATA.RET = rsp_p[8] | (rsp_p[9] << 8)
        RSP_DATA.Data = [0x00] * (RSP_DATA.LEN - 2)
        for i in range(len - 12):
            RSP_DATA.Data[i] = rsp_p[10 + i]
        RSP_DATA.CKS = rsp_p[len-2] | (rsp_p[len - 1] << 8)
    else:
        RSP.Prefix =rsp[0] + (rsp[1] << 8)
        RSP.SID = rsp[2] & 0xFF
        RSP.DID = rsp[3] & 0xFF
        RSP.RCM = rsp[4] | (rsp[5] << 8)
        RSP.LEN = rsp[6] | (rsp[7] << 8)
        RSP.RET = rsp[8] | (rsp[9] << 8)
        for i in range(14):
            RSP.Data[i] = rsp[10 + i]
        RSP.CKS = rsp[24] | (rsp[25] << 8)

#*********************************************
# Function: Receive a image data packet via serial port
# @param:
#       timeout: Timeout period to receive data packet
# @Return:
#       ERR_SUCCESS : Received Successful
#       ERR_FAIL : Receive Failed
#*********************************************
def Rx_Image_packet(timeout = 3):
    start_time = time.time()
    global rsp_p, rsp
    while time.time() - start_time < timeout:
        try:
            if ser.inWaiting():
                rsp = ser.read(26)
                #print("Received response:", [hex(x) for x in rsp])
                Rx_CMD_Process(1)
                if RSP.RCM != 0xFF:
                    checksum = 0
                    for i in range(24): # Calculate checksum for the first 24 bytes
                        checksum += rsp[i]
                    #print("received checksum:",hex(checksum))
                    if checksum == RSP.CKS:
                        #print("Checksum valid")
                        width = RSP.Data[0] + (RSP.Data[1] << 8)
                        height = RSP.Data[2] + (RSP.Data[4] << 8)
                        #print(f"Image size: width {width} height {height} ")
                        #if (width != Image_width / 2) or (height != Image_height / 2) or (width != Image_width) or (height != Image_height):
                        #    print("Wrong image size")
                        #    return ERR_FAIL
                        RSP_DATA.Data = [0x00]*(width * height)
                        packet_num = int ((width * height) / 496)
                        packet_last = int((width * height) % 496)
                        for i in range (packet_num):
                            rsp_p = [0x00] * 510
                            rsp_p = ser.read(510)
                            for j in range (496):
                                RSP_DATA.Data[i*496 + j] = rsp_p[j + 12]
                            #print ("the data packet received:", [hex(x) for x in rsp_p])

                        rsp_p = [0x00] * (packet_last + 14)
                        rsp_p = ser.read(packet_last + 14)
                        for j in range (packet_last):
                            RSP_DATA.Data[packet_num*496 + j] = rsp_p[j + 12]
                          
                        #print(f"Received response data: {[hex(x) for x in RSP_DATA.Data]} ; len {len(RSP_DATA.Data)}")
                        rsp = [0x00] * 26
                        return ERR.ERR_SUCCESS
                    else:
                        print("Checksum error")
                        return ERR.ERR_FAIL
                else:
                    print("Incorrect Command")
                    break
        except Exception as e:
            print("Error reading from serial port:", e)
            return ERR.ERR_FAIL    

#*********************************************
# Function: Receive a command vai serial port
# @param:
#       timeout: Timeout period to receive data packet
#       number: Number of bytes to receive
# @Return: 
#       ERR_SUCCESS : Received Successful
#       ERR_DATA : Data error
#*********************************************
def Rx_cmd(timeout = 3, number = 26):
    start_time = time.time()
    global rsp 
    while time.time() - start_time < timeout:
        try:
            if ser.inWaiting():
                read_bytes = ser.read(number)
                for i in range(len(read_bytes)):
                    rsp[i] = read_bytes[i]
                #print("Received response:", [hex(x) for x in rsp])
                Rx_CMD_Process(1)
                if RSP.RCM != 0xFF:
                    checksum = 0
                    for i in range(24): # Calculate checksum for the first 24 bytes
                        checksum += rsp[i]
                    #print("received checksum:",hex(checksum))
                    if checksum == RSP.CKS or number < 26:
                        #print("Checksum valid")
                        rsp = [0x00] * 26
                        return ERR.ERR_SUCCESS
                    else:
                        print("Checksum error")
                        return ERR.ERR_FAIL
                else:
                    print("Incorrect Command")
                    break
        except Exception as e:
            print("Error reading from serial port:", e)
            return ERR.ERR_FAIL

#*********************************************
# Function: Receive a data packet vai serial port
# @param:
#       timeout: Timeout period to receive data packet
# @Return: 
#       ERR_SUCCESS : Received Successful
#       ERR_FAIL: Receive Failed
#*********************************************
def Rx_data_cmd(timeout = 3):
    start_time = time.time()
    global rsp_p, rsp
    while time.time() - start_time < timeout:
        try:
            if ser.inWaiting():
                rsp = ser.read(26)
                #print("Received response:", [hex(x) for x in rsp])
                Rx_CMD_Process(1)
                if RSP.RCM != 0xFF:
                    checksum = 0
                    for i in range(24): # Calculate checksum for the first 24 bytes
                        checksum += rsp[i]
                    #print("received checksum:",hex(checksum))
                    if checksum == RSP.CKS:
                        #print("Checksum valid")
                        len_packet = RSP.Data[0] + (RSP.Data[1] << 8) + 12
                        rsp_p = [0x00] * len_packet
                        rsp_p = ser.read(len_packet)
                        #print("Received response data:", [hex(x) for x in rsp_p])
                        Rx_CMD_Process(1, len = len_packet)
                        if RSP_DATA.RCM != 0xFF:
                            for i in range(len_packet - 2): # Calculate checksum 
                                checksum += rsp_p[i]
                            #print("received checksum:",hex(checksum))
                            if checksum == RSP_DATA.CKS:
                                #rsp_p = []
                                print("Receive data_packet successfully")
                        rsp = [0x00] * 26
                        return ERR.ERR_SUCCESS
                    else:
                        print("Checksum error")
                        return ERR.ERR_FAIL
                else:
                    print("Incorrect Command")
                    break
        except Exception as e:
            print("Error reading from serial port:", e)
            return ERR.ERR_FAIL

#*********************************************
# Function: Check device connection status
# @Return:
#       ERR_SUCCESS : Connected Successful
#       ERR_FAIL : Connection Failed
#*********************************************
def Test_Connection():
    SLED_CTL(0)
    CMD.CMD = CMD_TEST_CONNECTION
    #print("Test the connection status of device")
    SendCmd()
    ret = Rx_cmd()
    #if ret == ERR.ERR_SUCCESS:
        #print("Device is connected successully")
    #else:
        #print("Device is fail to connect, please check it agian")
    return ret

#*********************************************
# Function: Set the Paramere of device
# @param: 
#       Tyep_ID, The type of parameter to set, including:
#           'Dev_ID' : Device ID; range 1 ~ 255
#           'Secu_Level' : Security level; range 1 ~ 5
#           'Dup_Check' : Duplication Check status; 0: enable; 1: disable
#           'Baudrate' : Baudrate; 0:9600, 1:19200, 2:38400, 3:57600, 4:115200, 5:230400, 6:460800, 7:921600
#           'Auto_Learn' : Aduo Learn status; 0: enable; 1: disable
#       Param_Value, The value of parameter to set
# @Return:
#       ERR_SUCCESS : Set Successful
#       ERR_FAIL : Set Failed
#*********************************************
def Set_Param(Type='Dev_ID', Param_Value = 1):
    CMD.CMD = CMD_SET_PARAM
    CMD.LEN = 5
    CMD.Data[0] = Param[Type]
    flag = 1
    match Param[Type]:
        case 0x00:
            if (Param_Value < 0) or (Param_Value > 255):
                print("The ID is invalid, should be in range (1 ~ 255)")
                flag = 0
        case 0x01:
            if (Param_Value < 1) or (Param_Value > 5):
                print ("Invalid value, should be in range (1 ~ 5)")
                flag = 0
        case 0x02:
            if  Param_Value not in (0, 1):
                print("Invalid value, should be 0: Disable; 1: Enable")
                flag = 0
        case 0x03:
            if (Param_Value < 1) or (Param_Value > 8):
                print("Wrong Seeting, should be 1:9600, 2:19200, 3:38400, 4:57600, 5:115200, 6:230400, 7:460800, 8:921600 ")
                flag = 0
        case 0x04:
            if Param_Value not in (0, 1):
                print("Invalid value, should be 0: Disable; 1： Enable")
                flag = 0
        case _:
            print("Unkown Type")
            flag = 0
    if flag:
        value = Param_Value & 0xFFFFFFFF
        CMD.Data[1] = value & 0xFF
        CMD.Data[2] = (value << 8) & 0xFF
        CMD.Data[3] = (value << 16) & 0xFF
        CMD.Data[4] = (value << 24) & 0xFF
        SendCmd()
        ret = Rx_cmd()
        if ret == ERR.ERR_SUCCESS:
            print("Set the Device Paramter successfully")
            return ERR.ERR_SUCCESS
        return RSP.RET
    else:
        return RSP.RET


#*********************************************
# Function: Get the Paramete of device
# @param: 
#       Type_ID, The type of parameter to get, including:
#           'Dev_ID' : Device ID; range 1 ~ 255
#           'Secu_Level' : Security level; range 1 ~ 5
#           'Dup_Check' : Duplication Check status; 0: enable; 1: disable
#           'Baudrate' : Baudrate; 0:9600, 1
#           'Auto_Learn' : Aduo Learn status; 0: enable; 1: disable
# @Return:
#   ERR_SUCCESS : Get Successful
#   ERR_FAIL : Get Failed
#*********************************************
def Get_Param(Type = 'Dev_ID'):
    CMD.CMD = CMD_GET_PARAM
    CMD.LEN = 1
    CMD.Data[0] = Param[Type]
    info = 0
    SendCmd()
    ret = Rx_cmd()
    if ret == ERR.ERR_SUCCESS:
        info = (RSP.Data[0] & 0xFF) + ((RSP.Data[1] << 8) & 0xFF) + ((RSP.Data[2] << 16) & 0xFF) + ((RSP.Data[3] << 24) & 0xFF)
        #print(f"The {Type} of the Device is: {info}")
        return ERR.ERR_SUCCESS, info
    print("fail to get paramet")
    return ERR.ERR_FAIL
    
#*********************************************
# Function: Get device information
# @Return:
#       ERR_SUCCESS : Get Successful
#       ERR_FAIL : Get Failed
#       info: Device information string
#*********************************************
def Get_DevInfo():
    CMD.CMD = CMD_DEVICE_INFO
    CMD.LEN = 0
    info = None
    SendCmd()
    ret = Rx_data_cmd()
    if ret == ERR.ERR_SUCCESS:
        info = bytes(RSP_DATA.Data).decode('utf-8', errors = 'replace')
        #print("The Device is:", info)
        return RSP.RET, info
    return RSP.RET, info

#*********************************************
# @Function: Acquire fingerprint image and save to imagebuffer
# @Return:
#       ERR_SUCCESS : Acquire Successful
#       ERR_FAIL : Acquire Failed
#*********************************************
def Get_FP_Image():
    CMD.CMD = CMD_GET_IMAGE
    SendCmd()
    ret = Rx_cmd()
    SLED_CTL(0)
    if ret == ERR.ERR_SUCCESS:
        #print("Acquire fingerprint image successuflly and save to Imagebuffer")
        return RSP.RET
    else:
        #print("Fail to acquire fingerprint image")
        return RSP.RET

#*********************************************
# Function: Check finger is placed on sensor or not
# @Return:
#       ERR_SUCCESS : Finger is detected
#       ERR_FAIL : Finger is not detected
#*********************************************
def Check_Finger():
    SLED_CTL(1)
    CMD.CMD = CMD_FINGER_DETECT
    SendCmd()
    ret = Rx_cmd()
    if ret == ERR.ERR_SUCCESS and RSP.Data[0] == 1:
        #SLED_CTL(0)
        #print("Finger is detected")
        return RSP.RET
    else:
        #SLED_CTL(0)
        #print("fail to detect finger")
        return RSP.RET

#*********************************************
# Function: Control sensor LED
# @param:
#       flag: LED control flag
#           0: Turn off LED
#           1: Turn on LED
# @Return:
#       ERR_SUCCESS : Command Successful
#       ERR_FAIL : Command Failed
#*********************************************
def SLED_CTL(flag):
    CMD.CMD = CMD_SLED_CTRL
    CMD.LEN = 2
    CMD.Data[0] = flag & 0xFF
    CMD.Data[1] = (flag >> 8) & 0xFF
    SendCmd()
    ret = Rx_cmd()
    if ret == ERR.ERR_SUCCESS:
        return RSP.RET
    else:
        return RSP.RET

#*********************************************
# Function: Get fingerprint image from imagebuffer and upload to host device
# @param:
#       type: Image type
#           0: Full image (192x192)
#           1: Quarter image (96x96)
#       file_name: The name of saved image file
# @Return:
#       ERR_SUCCESS : Send Successful
#       ERR_FAIL : Send Failed
#*********************************************
def UP_Image(ID = 1, type = 1, file_name = "finger_image"):
    CMD.CMD = CMD_UP_IMAGE_CODE
    CMD.LEN = 1
    CMD.Data[0] = type
    SendCmd()
    ret = Rx_Image_packet()
    if ret == ERR.ERR_SUCCESS:
        if type:
            save_quater_image(file_name)
        elif type == 0:
            save_full_image(file_name)
            None
        else:
            print("Unknown image type")
            return ERR.ERR_INVALID_PARAM
        return RSP.RET
    else:
        return RSP.RET

#*********************************************
#Function: Save quarter image to PNG file and TXT file
#@param:
#       file_name: The name of saved image file
#@return: None
#*********************************************
def save_quater_image(file_name = "FP_image"):
    width = int(Image_width / 2)
    height = int(Image_height / 2)
    if not os.path.exists("Pic"):
        os.makedirs("Pic")
    if not os.path.exists("Template"):
        os.makedirs("Template")
    #time_str = time.localtime()
    #time = f"{time_str.tm_year}{time_str.tm_mon:02d}{time_str.tm_mday:02d}_{time_str.tm_hour:02d}{time_str.tm_min:02d}{time_str.tm_sec:02d}"

    if len(RSP_DATA.Data) != (width * height):
        print("wrong image data lenth")
        return ERR.ERR_FAIL
    print("handle the image now")
    image_path =f"Pic/{file_name}.bmp"
    txt_path = f"Template/{file_name}.txt"
    #mode1_flat = np.random.randint(0, 256, width*height, dtype=np.uint8).tolist()
    data_array = np.array(RSP_DATA.Data).reshape(width, height)
    image_array = np.zeros((Image_width,Image_height), dtype=data_array.dtype)

    for i in range (width):
        for j in range (height):
            value = data_array[i,j]
            image_array[2*i, 2*j] = value
            image_array[2*i, 2*j + 1] = value
            image_array[2*i + 1, 2*j] = value
            image_array[2*i + 1, 2*j + 1] = value

    image = Image.fromarray(image_array.astype(np.uint8))
    image.save(image_path, dpi=(508,508))
    print("Image is save to ",os.path.abspath(image_path))

    with open(txt_path, "w") as f:
        for i in range(image_array.shape[0]):
            for j in range(image_array.shape[1]):
                pixel_value = image_array[i, j]
                f.write(f"{hex(pixel_value)} ")
            f.write("\n")
    print("The image data is save to: ", os.path.abspath(txt_path))

#*********************************************
#Function: Save full image to bmp file and TXT file
#@param:
#       file_name: The name of saved image file
#@return: None
#*********************************************
def save_full_image(file_name = "FP_image"):
    width = int(Image_width)
    height = int(Image_height)
    if not os.path.exists("Pic"):
        os.makedirs("Pic")
    if not os.path.exists("Template"):
        os.makedirs("Template")

    if len(RSP_DATA.Data) != (width * height):
        print("wrong image data lenth")
        return ERR.ERR_FAIL
    print("handle the image now")
    image_path =f"Pic/{file_name}.bmp"
    txt_path = f"Template/{file_name}.txt"
    #mode1_flat = np.random.randint(0, 256, width*height, dtype=np.uint8).tolist()
    data_array = np.array(RSP_DATA.Data).reshape(width, height)
    image_array = np.zeros((Image_width,Image_height), dtype=data_array.dtype)

    for i in range (width):
        for j in range (height):
            image_array[i,j] = data_array[i,j]

    image = Image.fromarray(image_array.astype(np.uint8))
    image.save(image_path, dpi=(508,508))
    print("Image is save to ",os.path.abspath(image_path))

    with open(txt_path, "w") as f:
        for i in range(image_array.shape[0]):
            for j in range(image_array.shape[1]):
                pixel_value = image_array[i, j]
                f.write(f"{hex(pixel_value)} ")
    print("The image data is save to: ", os.path.abspath(txt_path))

#*********************************************
#Function: Download fingerprint image from host device to imagebuffer
#@param:
#       file_name: The name of image file to download
#Return:
#   ERR_SUCCESS : Download Successful
#   ERR_FAIL : Download Failed
#*********************************************
def Down_Image(file_name = "FP_Image"):
    CMD.CMD = CMD_DOWN_IMAGE
    width = Image_width 
    height = Image_height
    CMD.LEN = 4
    CMD.Data[0] = width & 0xFF
    CMD.Data[1] = (width >> 8) & 0xFF
    CMD.Data[2] = height & 0xFF
    CMD.Data[3] = (height >> 8) & 0xFF
    SendCmd()
    ret = Rx_cmd()
    if ret != ERR.ERR_SUCCESS:
        print("Fail to send down image command")
        return ERR.ERR_FAIL
    image_file = f"Template/{file_name}.txt"
    if not os.path.exists(image_file):
        print("The image file does not exist")
        return ERR.ERR_FAIL
    Send_Packet(image_file, width, height)
    ret = Rx_cmd()
    if ret == ERR.ERR_SUCCESS:
        print("Download image to device successfully")
        return ERR.ERR_SUCCESS

def Get_Empty_ID(BeginID = 1, EndID = 1000):
    CMD.CMD = CMD_GET_EMPTY_ID
    CMD.LEN = 4
    CMD.Data[0] = BeginID & 0xFF
    CMD.Data[1] = (BeginID >> 8) & 0xFF
    CMD.Data[2] = EndID & 0xFF
    CMD.Data[3] = (EndID >> 8) & 0xFF
    SendCmd()
    ret = Rx_cmd()
    if ret == ERR.ERR_SUCCESS:
        empty_id = RSP.Data[0] + (RSP.Data[1] << 8)
        print(f"The empty ID is: {empty_id}")
        return ERR.ERR_SUCCESS, empty_id
    else:
        print("Fail to get empty ID")
        return ERR.ERR_FAIL, None

#*********************************************
# Function: Generate fingerprint template from imagebuffer
# @param:
#       BufID: Buffer ID to store the generated template, 0 or 1 or 2
# @Return:
#       ERR_SUCCESS : Generate Successful
#       ERR_FAIL : Generate Failed
#*********************************************
def Generate_Template(BufID = 0):
    CMD.CMD = CMD_GENERATE
    CMD.LEN = 2
    CMD.Data[0] = BufID & 0xFF  # Buffer ID
    CMD.Data[1] = (BufID >> 8) & 0xFF
    SendCmd()
    ret = Rx_cmd()
    if ret == ERR.ERR_SUCCESS:
        #print("Generate template successfully")
        return RSP.RET
    else:
        print("Fail to generate template")
        return RSP.RET

def Merge_Template(BufID = 1, num = 2):
    CMD.CMD = CMD_MERGE
    CMD.LEN = 3
    CMD.Data[0] = BufID & 0xFF  # Buffer ID
    CMD.Data[1] = (BufID >> 8) & 0xFF
    CMD.Data[2] = num  # Merge count
    SendCmd()
    ret = Rx_cmd()
    if ret == ERR.ERR_SUCCESS:
        #print("Merge template successfully")
        return RSP.RET
    else:
        #print("Fail to merge template")
        return RSP.RET

def Match_Template(BufID_1 = 0, BufID_2 = 1):
    CMD.CMD = CMD_MATCH
    CMD.LEN = 4
    CMD.Data[0] = BufID_1 & 0xFF  # Buffer ID 1
    CMD.Data[1] = (BufID_1 >> 8) & 0xFF
    CMD.Data[2] = BufID_2 & 0xFF  # Buffer
    CMD.Data[3] = (BufID_2 >> 8) & 0xFF
    SendCmd()
    ret = Rx_cmd()
    if ret == ERR.ERR_SUCCESS:
        score = RSP.Data[0] + (RSP.Data[1] << 8)
        print(f"Match successfully, score: {score}")
        return RSP.RET, score
    else:
        print("Fail to match template")
        return RSP.RET, None

#*********************************************
# Function: Search fingerprint template in database (1:N)
# @param:
#       BufID: Buffer ID to store the generated template, 0 or 1 or 2
#       BeginID: Begin ID to search
#       EndID: End ID to search 
# @Return:
#       ERR_SUCCESS : Search Successful
#       ERR_FAIL : Search Failed
#       found_id: The found ID
#       score: The auto_update status
#*********************************************
def Search_Template(BufID = 0, BeginID = 1, EndID = 1000):
    CMD.CMD = CMD_SEARCH
    CMD.LEN = 6
    CMD.Data[0] = BufID & 0xFF  # Buffer ID
    CMD.Data[1] = (BufID >> 8) & 0xFF
    CMD.Data[2] = BeginID & 0xFF
    CMD.Data[3] = (BeginID >> 8) & 0xFF
    CMD.Data[4] = EndID & 0xFF
    CMD.Data[5] = (EndID >> 8) & 0xFF
    SendCmd()
    ret = Rx_cmd()
    if ret == ERR.ERR_SUCCESS and RSP.LEN != 2:
        found_id = RSP.Data[0] + (RSP.Data[1] << 8)
        score = RSP.Data[2] + (RSP.Data[3] << 8)
        #print(f"Search successfully, found ID: {found_id}, score: {score}")
        return RSP.RET, found_id, score
    else:
        print("Fail to search template")
        return RSP.RET, None, None

#*********************************************
# Function: Verify fingerprint template in database (1:1)
# @param:
#       BufID: Buffer ID to store the generated template, 0 or 1 or 2
#       ID: ID to verify
# @Return:
#       ERR_SUCCESS : Verify Successful
#       ERR_FAIL : Verify Failed
#       found_id: The found ID
#       score: The auto_update status
#*********************************************
def Verify_Template(BufID = 0, ID = 1):
    CMD.CMD = CMD_VERIFY
    CMD.LEN = 4
    CMD.Data[0] = ID & 0xFF  # Buffer ID
    CMD.Data[1] = (ID >> 8) & 0xFF
    CMD.Data[2] = BufID & 0xFF
    CMD.Data[3] = (BufID >> 8) & 0xFF
    SendCmd()
    ret = Rx_cmd()
    if ret == ERR.ERR_SUCCESS and RSP.LEN != 2:
        found_id = RSP.Data[0] + (RSP.Data[1] << 8)
        score = RSP.Data[2] + (RSP.Data[3] << 8)
        #print(f"Search successfully, found ID: {found_id}, score: {score}")
        return RSP.RET, found_id, score
    else:
        print("Fail to verify template")
        return RSP.RET, None, None

#*********************************************
# Function: Get enrolled ID list from device
# @Return:
#       ERR_SUCCESS : Get Successful
#       ERR_FAIL : Get Failed
#       id_list: The list of enrolled IDs and their status
#*********************************************
def Get_Enrolled_ID_List():
    CMD.CMD = CMD_GET_ENROLLED_ID_LIST
    CMD.LEN = 0
    SendCmd()
    ret = Rx_data_cmd()
    if ret == ERR.ERR_SUCCESS:
        id_list = []
        total_ids = RSP_DATA.LEN - 2
        for i in range(total_ids):
            current_byte = RSP_DATA.Data[i]
            for bit_pos in range(8):
                id = i * 8 + bit_pos
                is_registered = current_byte & (1 << bit_pos)
                id_list.append((id, is_registered))
        print(f"Enrolled ID List: {id_list}")
        return RSP.RET, id_list
    else:
        print("Fail to get enrolled ID list")
        return RSP.RET, None 

#*********************************************
# Function: Get Template ID status
# @param:
#       ID: ID to get status
# @Return:
#       ERR_SUCCESS : Get Successful
#       ERR_FAIL : Get Failed
#       status: The status of the ID, 0: not enrolled, 1: enrolled 
#*********************************************
def Get_Status(ID = 0):
    CMD.CMD = CMD_GET_STATUS
    CMD.LEN = 2
    CMD.Data[0] = ID & 0xFF  # Buffer ID
    CMD.Data[1] = (ID >> 8) & 0xFF
    SendCmd()
    ret = Rx_cmd()
    if ret == ERR.ERR_SUCCESS:
        status = RSP.Data[0]
        print(f"Device Status: {status}")
        return RSP.RET, status
    else:
        print("Fail to get device status")
        return RSP.RET, None   

#*********************************************
# Function: Store fingerprint template from buffer to database
# @param:
#       ID: ID to store template
#       BufID: Buffer ID to get the generated template, 0 or 1 or 2
# @Return:   
#       ERR_SUCCESS : Store Successful
#       ERR_FAIL : Store Failed
#*********************************************
def Store_Template(ID = 1, BufID = 0):
    CMD.CMD = CMD_STORE_CHAR
    CMD.LEN = 4
    CMD.Data[0] = ID & 0xFF  # ID
    CMD.Data[1] = (ID >> 8) & 0xFF
    CMD.Data[2] = BufID & 0xFF  # Buffer ID
    CMD.Data[3] = (BufID >> 8) & 0xFF
    SendCmd()
    ret = Rx_cmd()
    if ret == ERR.ERR_SUCCESS:
        print("Store template successfully")
        return RSP.RET
    else:
        print("Fail to store template")
        return RSP.RET

#*********************************************
# Function: Delete fingerprint template from database
# @param:
#       BeginID: Begin ID to delete
#       EndID: End ID to delete
# @Return:
#       ERR_SUCCESS : Delete Successful
#       ERR_FAIL : Delete Failed
# *********************************************    
def Delete_Template(BeginID = 1, EndID = 1000):
    CMD.CMD = CMD_DEL_CHAR
    CMD.LEN = 4
    CMD.Data[0] = BeginID & 0xFF  # Begin ID
    CMD.Data[1] = (BeginID >> 8) & 0xFF
    CMD.Data[2] = EndID & 0xFF  # End ID
    CMD.Data[3] = (EndID >> 8) & 0xFF
    SendCmd()
    ret = Rx_cmd()
    if ret == ERR.ERR_SUCCESS:
        print("Delete template successfully")
        return RSP.RET
    else:
        print("Fail to delete template")
        return RSP.RET

#*********************************************
# Function: Get enrolled fingerprint count from database
# @param:
#       BeginID: Begin ID to count
#       EndID: End ID to count
# @Return:
#       ERR_SUCCESS : Get Successful
#       ERR_FAIL : Get Failed
#       Count: The number of enrolled fingerprints
#*********************************************
def Get_Enroll_Count(BeginID = 1, EndID = 1000):
    CMD.CMD = CMD_GET_ENROLL_COUNT
    CMD.LEN = 4
    CMD.Data[0] = BeginID & 0xFF  # Begin ID
    CMD.Data[1] = (BeginID >> 8) & 0xFF
    CMD.Data[2] = EndID & 0xFF  # End ID
    CMD.Data[3] = (EndID >> 8) & 0xFF
    SendCmd()
    ret = Rx_cmd()
    if ret == ERR.ERR_SUCCESS and RSP.LEN != 2:
        count = RSP.Data[0] + (RSP.Data[1] << 8)
        #print(f"Enroll Count: {count}")
        return RSP.RET, count
    else:
        print("Fail to get enroll count")
        return RSP.RET, None