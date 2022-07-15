import re
import os
import hashlib
import license.maker as maker
from pathlib import Path
from datetime import datetime
from license.getmac import get_mac_address as gma
class action:
	def __init__(self,path):
		self.system_path = path

	def generate_key(self,input_key):
		Mac = gma().lower()
		if (Mac == "00:00:00:00:00:00"):
			print("Error For Activation, Please Contact Administrator !!!")
		elif re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", Mac):
			Mac_List = Mac.split(":")
		else:
			print("Error For Activation, Please Contact Administrator !!!")
		Reference_Number = maker.Reference_Number_Maker(Mac_List)

		File_License_Key_Content = ""
		File_License_Key = Path(self.system_path+"/KEY.txt")
		if File_License_Key.exists():
			with open(self.system_path+'/KEY.txt', 'r', encoding="utf-8") as f:
				File_License_Key_Content = f.read()

			if(len(File_License_Key_Content)!=640):
				os.remove(self.system_path+"/KEY.txt")
				print("Key File Damaged, Please Do Reactivation")
			else:
				if(maker.License_Key_TXT_Maker(maker.License_Key_Maker(Reference_Number))==File_License_Key_Content):
					print("Activation Successful !!!")
				else:
					os.remove(self.system_path+"/KEY.txt")
					print("Key File Damaged, Please Do Reactivation")
		else:
			print(f"Reference Number:{Reference_Number}")

		License_Key = maker.License_Key_Maker(Reference_Number)
		if '-' not in License_Key:
			input_key = input_key.replace('-', '') 

		if License_Key == input_key:
			License_Key_To_TXT = maker.License_Key_TXT_Maker(License_Key)
			with open(self.system_path+"/KEY.txt", "w+") as f:
				f.write(License_Key_To_TXT)
			print("Activation Successful")
		else:
			print("Activation Failed") 

	def activation_check(self,hash):
		Check_Received_Hash = datetime.today().strftime("*M."+'%m-%Y/%d>%H+%M')
		Return_Hash = Check_Received_Hash.replace("*M.", '')+".R&" 
		Return_Hash = hashlib.md5(Return_Hash.encode()).hexdigest()
		if(hashlib.md5(Check_Received_Hash.encode()).hexdigest()==hash):
			Mac = gma().lower()
			if (Mac == "00:00:00:00:00:00"):
				return {"status": "inauthentic","hash" : Return_Hash} 
			elif re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", Mac):
				Mac_List = Mac.split(":")
			else:
				return {"status": "inauthentic","hash" : Return_Hash}

			Reference_Number = maker.Reference_Number_Maker(Mac_List)
			License_Key = maker.License_Key_Maker(Reference_Number)
			License_Key_To_TXT = maker.License_Key_TXT_Maker(License_Key)
			File_License_Key = Path(self.system_path+"/KEY.txt")
			if File_License_Key.exists():
				with open(self.system_path+'/KEY.txt', 'r', encoding="utf-8") as f:
					File_License_Key_Content = f.read()
				if(License_Key_To_TXT==File_License_Key_Content):
					return {"status": "authenticated","hash" : Return_Hash}
				else:
					return {"status": "hash_error"}   
			else:
				return {"status": "hash_error"}  
		else:
			return {"status": "hash_error"}

	def verify(self):
		Hash = datetime.today().strftime("*M."+'%m-%Y/%d>%H+%M')
		md5_Hash = hashlib.md5(Hash.encode()).hexdigest()
		response = self.activation_check(md5_Hash)
		status = response['status']
		verify = False
		if status == 'authenticated':
			return_hash = response['hash']
			md5_return_hash = Hash.replace("*M.", '') + ".R&"
			md5_return_hash = hashlib.md5(md5_return_hash.encode()).hexdigest()
			verify = (md5_return_hash==return_hash)
		return verify