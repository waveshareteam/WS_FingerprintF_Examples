import serial
import time
import threading 
import WS_fingerprintF as Fin

ERR_Code = Fin.ERR_Code()
Baudrate = {0:9600, 1:19200, 2:38400, 3:57600, 4:115200, 5:230400, 6:460800, 7:921600}

def Add_User():
    
    num = int(input("To add User, please input a ID in range 1 ~ 1000, put it to 0 if you want to use the default mini empty ID: "))
    if 1 <= num <= 1000:
        User_ID = num
    else:
        ret, ID = Fin.Get_Empty_ID()
        if ret ==  ERR_Code.ERR_SUCCESS:
            User_ID = ID
        else:
            print("Get empty ID failed, ret = ", ret)
            return ERR_Code.ERR_FAIL
    if Fin.Get_Status(User_ID)[1] == 0:
        print("Please put your finger on sensor")
        for step in range (3):
            print(f"Please {'lift' if step > 0 else ''} and put your finger on sensor again for step {step}")
            while Fin.Check_Finger():
                time.sleep(1)

            ret = Fin.Get_FP_Image()
            if ret == ERR_Code.ERR_SUCCESS:
                ret = Fin.Generate_Template(step)
                if ret != ERR_Code.ERR_SUCCESS:
                    print("Gen_Temp failed, ret = ", ret)
                    return ret
            
        ret = Fin.Merge_Template(BufID = 0, num = 3)
        if ret == ERR_Code.ERR_SUCCESS:
            ret = Fin.Store_Template(User_ID, BufID = 0)
            if ret == ERR_Code.ERR_SUCCESS:
                print(f"Enroll user {User_ID} successfully")
                return ERR_Code.ERR_SUCCESS
        else:
            print("Store_Temp failed, ret = ", ret)
            return ret

def Verify_User():
    type = int(input("Please input verify type: 0 - 1:1, 1 - 1:N: "))
    if type == 1:
        print("Please put your finger on sensor to verify user")
        while Fin.Check_Finger():
            time.sleep(1)

        ret = Fin.Get_FP_Image()
        if ret == ERR_Code.ERR_SUCCESS:
            ret = Fin.Generate_Template(BufID=0)
            if ret != ERR_Code.ERR_SUCCESS:
                #print("Gen_Temp failed, ret = ", ret)
                return ret
            ret, ID, score= Fin.Search_Template(BufID = 0)
            if ret == ERR_Code.ERR_SUCCESS:
                print(f"Verify user successfully, User ID = {ID}, Score ={score}")
                return ERR_Code.ERR_SUCCESS
            else:
                #print("Verify user failed, ret = ", ret)
                return ret
        else:
            #print("Get_FP_Image failed, ret = ", ret)
            return ret
    elif type == 0:
        User_ID = int(input("Please input User ID to verify(1 ~ 1000): "))
        print("Please put your finger on sensor to verify user")
        while Fin.Check_Finger():
            time.sleep(1)

        ret = Fin.Get_FP_Image()
        if ret == ERR_Code.ERR_SUCCESS:
            ret = Fin.Generate_Template(BufID=0)
            if ret != ERR_Code.ERR_SUCCESS:
                #print("Gen_Temp failed, ret = ", ret)
                return ret
            ret, ID, score = Fin.Verify_Template(BufID = 0, ID = User_ID)
            if ret == ERR_Code.ERR_SUCCESS:
                print(f"Verify user {User_ID} successfully, Score ={score}")
                return ERR_Code.ERR_SUCCESS
            else:
                #print("Verify user failed, ret = ", ret)
                return ret
        else:
            #print("Get_FP_Image failed, ret = ", ret)
            return ret
    else:
        print("Input type is invalid")
        return ERR_Code.ERR_FAIL

def Get_Device_AllInfo():
    ret, info = Fin.Get_DevInfo()
    if ret == ERR_Code.ERR_SUCCESS:
        print("Device Info: ", info)
    else:
        Process_ERR(ret)
        return ret
    ret,info = Fin.Get_Param(Type = "Dev_ID")
    if ret == ERR_Code.ERR_SUCCESS:
        print("Device ID: ", info)
    else:
        Process_ERR(ret)
        return ret
    ret,info = Fin.Get_Param(Type = "Secu_Level")
    if ret == ERR_Code.ERR_SUCCESS:
        print("Security Level: ", info)
    else:
        Process_ERR(ret)
        return ret
    ret,info = Fin.Get_Param(Type = "Dup_Check")
    if ret == ERR_Code.ERR_SUCCESS:
        print("Duplicate Check Status, 0-enable; 1-disable: ", info)
    else:
        Process_ERR(ret)
        return ret
    ret,info = Fin.Get_Param(Type = "Baudrate")
    if ret == ERR_Code.ERR_SUCCESS:
        print("Baudrate of device: ", Baudrate[info])
    else:
        Process_ERR(ret)
        return ret
    ret,info = Fin.Get_Param(Type = "Auto_Learn")
    if ret == ERR_Code.ERR_SUCCESS:
        print("Auto Learn Status, 0-enable; 1-disable: ", info)
    else:
        Process_ERR(ret)
        return ret
    ret,info = Fin.Get_Enroll_Count()
    if ret == ERR_Code.ERR_SUCCESS:
        print("Enrolled User Count: ", info)
    else:
        Process_ERR(ret)
        return ret
    
def Process_ERR(ret):
    ERR_Map = {
        0x00: "Command is processed successfully",   
        0x01: "Error receiving data package",
        0x10: "The fingerpint is fail to verify in 1:1 mode",     
        0x11: "The fingerprint is fail to search in 1:N mode",
        0x12: "The template is not found to be registered",
        0x13: "The Template already exists",
        0x14: "No registered templates in the database",
        0x15: "No vaild Template ID",
        0x16: "No broken Template",
        0x17: "The Template Data is invalid",
        0x18: "The fingerprint was existed",
        0x19: "Fingerprint image quanlity is too poor",
        0x1A: "Fail to marge the template",
        0x1C: "Fail to flashed",
        0x22: "Wrong parameter",
        0x25: "Invalid count of templates to marge",
        0x23: "Input fingerprint Timeout",
        0x26: "Wrong Buffer ID",
        0x28: "No finger detected on the sensor",
        0x41: "Command is cancel",
    }
    print("Error occurred: ", ERR_Map.get(ret, "Unknown Error Code"))

def Process_CMD(cmd):
    if cmd == '1':
        ret = Fin.Test_Connection()
        if ret == ERR_Code.ERR_SUCCESS:
            print("Test Connection successfully")
        else:
            Process_ERR(ret)

    elif cmd == '2':
        Get_Device_AllInfo()
    elif cmd == '3':
        Add_User()
    elif cmd == '4':
        Verify_User()
    elif cmd == '5':
        ret = Fin.Delete_Template()
        if ret == ERR_Code.ERR_SUCCESS:
            print("Delete all enrolled information successfully")
        else:
            print("Delete all enrolled information failed, ret = ", ret)
    elif cmd == '6':
        print("This operation will not enroll the fingerprint template into the database, if you need to enroll, please use Add User function")
        print("Get Fingerprint Image now, default save as 'FP_Image.png' in Pic folder")
        print("and the raw data save as 'FP_Image.txt' in Template folder")
        print("Note that this operation will overwrite the existing files with the same name")
        print("Please put your finger on sensor to get image")
        while Fin.Check_Finger():
            time.sleep(1)
        ret = Fin.Get_FP_Image()
        if ret == ERR_Code.ERR_SUCCESS:
            print("Getting the Image data now, please wait...")
            ret = Fin.UP_Image(file_name="FP_Image", type=1)
            if ret != ERR_Code.ERR_SUCCESS:
                Process_ERR(ret)

    elif cmd == '7':
        print("This operation will not enroll the fingerprint template into the database, if you need to enroll, please use Add User function")
        print("This operation will read the FP_image.txt file and save it to the imagebuff of the device")
    
        ret = Fin.Down_Image()
        if ret == ERR_Code.ERR_SUCCESS:
            print("Downloading the Image data to ImageBuff now, please wait...")
            ret = Fin.UP_Image_to_Buff()
            if ret == ERR_Code.ERR_SUCCESS:
                print("Download Image to ImageBuff successfully")
            else:
                Process_ERR(ret)
        else:
            Process_ERR(ret)
    else:
        print("Invalid CMD code")
def main():
 
    print("******This is the test codes for Waveshare Fingerprint Scanner Module F******")
    print("Please input the command Code to test corresponding function:")
    print("1: Test Connection;")
    print("2: Get Device info;")
    print("3: Add User;")
    print("4: Verify User;")
    print("4: Delete All the enrolled information;")
    print("6: Get Fingerprint Image;")
    #print("7: Download Fingerprint Image to ImageBuff;")
    while True:
        cmd = input("Please input CMD code (or 'exit' to quit): ")
        if cmd == 'exit':
            break 
        Process_CMD(cmd)
        time.sleep(1)

    print("Exiting the program.")   



if __name__ == "__main__":
    main()