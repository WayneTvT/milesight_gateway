import re
import hashlib
def Reference_Number_Maker(Mac_List):
    new_order_count = 1
    for l in Mac_List:
        if(new_order_count==1):
            new_order_mac_list_1  = l
        elif(new_order_count==2):
            new_order_mac_list_2  = l
        elif(new_order_count==3):
            new_order_mac_list_3  = l
        elif(new_order_count==4):
            new_order_mac_list_4  = l
        elif(new_order_count==5):
            new_order_mac_list_5  = l
        elif(new_order_count==6):
            new_order_mac_list_6  = l
        new_order_count+=1
    mac_list_new_ordering =  new_order_mac_list_5+"@"
    mac_list_new_ordering += new_order_mac_list_2+"^"
    mac_list_new_ordering += new_order_mac_list_6+"$"
    mac_list_new_ordering += new_order_mac_list_1+"!"
    mac_list_new_ordering += new_order_mac_list_4+"%"
    mac_list_new_ordering += new_order_mac_list_3+"#"
    Stage_1_Reference_Number = hashlib.md5(mac_list_new_ordering.encode()).hexdigest()
    Stage_2_Reference_Number =  Stage_1_Reference_Number[7:8]
    Stage_2_Reference_Number += Stage_1_Reference_Number[2:3]
    Stage_2_Reference_Number += Stage_1_Reference_Number[3:4]
    Stage_2_Reference_Number += Stage_1_Reference_Number[25:26]
    Stage_2_Reference_Number += Stage_1_Reference_Number[10:11]
    Stage_2_Reference_Number += Stage_1_Reference_Number[12:13]
    Stage_2_Reference_Number += Stage_1_Reference_Number[0:1]
    Stage_2_Reference_Number += Stage_1_Reference_Number[13:14]
    Stage_2_Reference_Number += Stage_1_Reference_Number[30:31]
    Stage_2_Reference_Number += Stage_1_Reference_Number[23:24]
    Stage_2_Reference_Number = Stage_2_Reference_Number.upper()
    return Stage_2_Reference_Number
def License_Key_Maker(Reference_Number):
    Stage_1_License_Key = hashlib.md5(Reference_Number.encode()+'happy guessing'.encode()).hexdigest() + \
                          hashlib.md5(Reference_Number.encode()).hexdigest()
    Stage_2_License_Key = Stage_1_License_Key[:20].upper()
    Stage_3_License_Key = '-'.join([Stage_2_License_Key[i:i+4] for i in range(0, len(Stage_2_License_Key), 4)])
    return Stage_3_License_Key
def License_Key_TXT_Maker(License_Key):
    License_Key_RE = re.findall(".",str(License_Key))
    License_Key_To_TXT =  hashlib.md5(("$@%^!#"+License_Key_RE[0]+"*)&(").encode()).hexdigest()
    License_Key_To_TXT += hashlib.md5(("$@%^!#"+License_Key_RE[1]+"*)&(").encode()).hexdigest()
    License_Key_To_TXT += hashlib.md5(("$@%^!#"+License_Key_RE[2]+"*)&(").encode()).hexdigest()
    License_Key_To_TXT += hashlib.md5(("$@%^!#"+License_Key_RE[3]+"*)&(").encode()).hexdigest()
    License_Key_To_TXT += hashlib.md5(("$@%^!#"+License_Key_RE[4]+"*)&(").encode()).hexdigest()
    License_Key_To_TXT += hashlib.md5(("$@%^!#"+License_Key_RE[5]+"*)&(").encode()).hexdigest()
    License_Key_To_TXT += hashlib.md5(("$@%^!#"+License_Key_RE[6]+"*)&(").encode()).hexdigest()
    License_Key_To_TXT += hashlib.md5(("$@%^!#"+License_Key_RE[7]+"*)&(").encode()).hexdigest()
    License_Key_To_TXT += hashlib.md5(("$@%^!#"+License_Key_RE[8]+"*)&(").encode()).hexdigest()
    License_Key_To_TXT += hashlib.md5(("$@%^!#"+License_Key_RE[9]+"*)&(").encode()).hexdigest()
    License_Key_To_TXT += hashlib.md5(("$@%^!#"+License_Key_RE[10]+"*)&(").encode()).hexdigest()
    License_Key_To_TXT += hashlib.md5(("$@%^!#"+License_Key_RE[11]+"*)&(").encode()).hexdigest()
    License_Key_To_TXT += hashlib.md5(("$@%^!#"+License_Key_RE[12]+"*)&(").encode()).hexdigest()
    License_Key_To_TXT += hashlib.md5(("$@%^!#"+License_Key_RE[13]+"*)&(").encode()).hexdigest()
    License_Key_To_TXT += hashlib.md5(("$@%^!#"+License_Key_RE[14]+"*)&(").encode()).hexdigest()
    License_Key_To_TXT += hashlib.md5(("$@%^!#"+License_Key_RE[15]+"*)&(").encode()).hexdigest()
    License_Key_To_TXT += hashlib.md5(("$@%^!#"+License_Key_RE[16]+"*)&(").encode()).hexdigest()
    License_Key_To_TXT += hashlib.md5(("$@%^!#"+License_Key_RE[17]+"*)&(").encode()).hexdigest()
    License_Key_To_TXT += hashlib.md5(("$@%^!#"+License_Key_RE[18]+"*)&(").encode()).hexdigest()
    License_Key_To_TXT += hashlib.md5(("$@%^!#"+License_Key_RE[19]+"*)&(").encode()).hexdigest()
    return License_Key_To_TXT