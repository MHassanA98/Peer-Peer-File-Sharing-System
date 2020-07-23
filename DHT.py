import socket
import threading
import os
import time
import hashlib
import pickle

'''
All the files owned by a node are already backed up on it's predecessor. When a node fails, it's
predecessor sends those files to the successor of the failed node which then becomes the owner of those files.
On the other other hand, to store the backup of the files of failed node's successor, the second
successor sends its files to the predecessor of the failed node. It's better to store the backup on a
predecessor since it stores not only the address of it's immediate successor, but also the address
of it's successor's successor. That's why the DHT can easily be stabilized without losing any files.

'''


class Node:
	def __init__(self, host, port):
		self.stop = False
		self.host = host
		self.port = port
		self.M = 16
		self.N = 2**self.M
		self.key = self.hasher(host+str(port))
		# You will need to kill this thread when leaving, to do so just set self.stop = True
		threading.Thread(target = self.listener).start()
		self.files = []
		self.backUpFiles = []
		if not os.path.exists(host+"_"+str(port)):
			os.mkdir(host+"_"+str(port))
		'''
		------------------------------------------------------------------------------------
		DO NOT EDIT ANYTHING ABOVE THIS LINE
		'''
		# Set value of the following variables appropriately to pass Intialization test
		self.successor = (host,port)
		self.predecessor = (host,port)
		self.secondSuccessor = (host,port)
		threading.Thread(target = self.Ping).start()
		self.FileFound=" "
		self.pingFail=0
		# additional state variables



	def hasher(self, key):
		'''
		DO NOT EDIT THIS FUNCTION.
		You can use this function as follow:
			For a node: self.hasher(node.host+str(node.port))
			For a file: self.hasher(file)
		'''
		return int(hashlib.md5(key.encode()).hexdigest(), 16) % self.N


	def handleConnection(self, client, addr):
		'''
		 Function to handle each inbound connection, called as a thread from the listener.
		'''

		message= client.recv(4096)
		message=pickle.loads(message)

		
		
		if message[0]=="JOIN":

			if self.predecessor==(self.host,self.port) and self.successor==(self.host,self.port):	#Case where only one node in the network

				sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.connect(message[1])
				
				self.successor=message[1]
				self.predecessor=message[1]
				self.secondSuccessor=(self.host,self.port)

				SendMessage=pickle.dumps( ["JOIN_SINGLE",(self.host,self.port)])
				sock.send(SendMessage)
				sock.close()

				time.sleep(0.5)

				delIt=[]
				for file in self.files:
					if self.hasher(file)<=self.hasher(self.predecessor[0]+str(self.predecessor[1])):

						File= os.getcwd()+"/"+self.host+"_"+str(self.port)+"/"+file
						sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
						sock.connect(self.predecessor)	#Put file at 
						SendMessage=pickle.dumps(["PUT",file])
						 
						sock.send(SendMessage)
						time.sleep(0.5)
						self.sendFile(sock,File)
						sock.close()
						delIt.append(file)
				
				for file in delIt:
					self.files.remove(file)

			
			else:	# Case where multiple nodes so need to lookup
				self.Lookup(message)

		elif message[0]=="LOOKUP":	#Lookup

			self.Lookup(message[1])

		elif message[0]=="JOIN_SINGLE":	#Reply for case where only one node in network
			self.successor=message[1]
			self.predecessor=message[1]
			self.secondSuccessor=(self.host,self.port)

		elif message[0]=="JOIN_MULTIPLE_SUCC":	#Reply for case when multiple nodes in network

			self.successor=message[1]
			self.secondSuccessor=message[2]

		elif message[0]=="PRED_CHECK":	#Ask successor for its predecessor

			sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.connect(message[1])

			SendMessage=pickle.dumps(["PRED_SEND",self.predecessor])
			sock.send(SendMessage)
			sock.close()

		
		elif message[0]=="PRED_SEND":	#Reply where successor sends back its predecessor


			if message[1]!=(self.host,self.port):	#successor's predecessor not equal (self.host,self.port)

				self.secondSuccessor=self.successor
				self.successor=message[1]

				sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.connect(self.successor)

				SendMessage=pickle.dumps(["PRED_UPDATE",(self.host,self.port)])
				sock.send(SendMessage)
				sock.close()

				sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.connect(self.predecessor)

				SendMessage=pickle.dumps(["SECOND_SUCC_UPDATE",self.successor])
				sock.send(SendMessage)
				sock.close()

				delIt=[]
				for file in self.backUpFiles:
					if self.hasher(file)>self.hasher(self.successor[0]+str(self.successor[1])):
						delIt.append(file)
				
				for file in delIt:
					self.backUpFiles.remove(file)

		elif message[0]=="SECOND_SUCC_UPDATE":

			self.secondSuccessor=message[1]

		elif message[0]=="PRED_UPDATE":	#Predecessor asking to be updated

			self.predecessor=message[1]
		
		elif message[0]=="SUCC_UPDATE":	#Successor asking to be updated
			
			self.successor=message[1]
			self.secondSuccessor=message[2]
			
			sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.connect(self.predecessor)
			SendMessage=pickle.dumps(["SECOND_SUCC_UPDATE",message[1]])
			sock.send(SendMessage)
			sock.close()

		elif message[0]=="PUT":	#Put files in directory, ask pred to backup the file

			self.files.append(message[1])	
			File= os.getcwd()+"/"+self.host+"_"+str(self.port)+"/"+message[1]
			self.recieveFile(client,File)

			sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.connect(self.predecessor)
			SendMessage=pickle.dumps(["PUT_BACK",message[1]])
			sock.send(SendMessage)
			time.sleep(0.5)
			self.sendFile(sock,File)
			sock.close()

		elif message[0]=="PUT_BACK":

			if message[1] not in self.backUpFiles:
				self.backUpFiles.append(message[1])	
				File= os.getcwd()+"/"+self.host+"_"+str(self.port)+"/"+message[1]
				self.recieveFile(client,File)

		elif message[0]=="GET":

			sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.connect(message[2])

			if message[1] in self.files:
				SendMessage=pickle.dumps(["GET_DONE",message[1]])
			else:
				SendMessage=pickle.dumps(["GET_DONE","None"])
				
			sock.send(SendMessage)
			sock.close()
		
		elif message[0]=="GET_DONE":
			self.FileFound=message[1]

		elif message[0]=="PING_FAIL":

			self.predecessor=message[1]
			
			sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.connect(self.predecessor)
			SendMessage=pickle.dumps(["SUCC_UPDATE",(self.host,self.port),self.successor])
			sock.send(SendMessage)
			sock.close()

			for file in self.files:

				File= os.getcwd()+"/"+self.host+"_"+str(self.port)+"/"+file
				sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.connect(self.predecessor)
				SendMessage=pickle.dumps(["PUT_BACK",file])
				sock.send(SendMessage)
				self.sendFile(sock,File)
				sock.close()


	def listener(self):
		'''
		We have already created a listener for you, any connection made by other nodes will be accepted here.
		For every inbound connection we spin a new thread in the form of handleConnection function. You do not need
		to edit this function. If needed you can edit signature of handleConnection function, but nothing more.
		'''
		listener = socket.socket()
		listener.bind((self.host, self.port))
		listener.listen(10)
		while not self.stop:
			client, addr = listener.accept()
			threading.Thread(target = self.handleConnection, args = (client, addr)).start()
		 
		try:
			listener.shutdown(2)
			listener.close()
		except:
			listener.close()

	def join(self, joiningAddr):
		'''
		This function handles the logic of a node joining. This function should do a lot of things such as:
		Update successor, predecessor, getting files, back up files. SEE MANUAL FOR DETAILS.
		'''

		if joiningAddr=="":
			return


		sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect(joiningAddr)


		message=pickle.dumps(["JOIN",(self.host, self.port),self.key])
		sock.send(message)
		sock.close()


	def put(self, fileName):
		
		'''
		This function should first find node responsible for the file given by fileName, then send the file over the socket to that node
		Responsible node should then replicate the file on appropriate node. SEE MANUAL FOR DETAILS. Responsible node should save the files
		in directory given by host_port e.g. "localhost_20007/file.py".
		'''
		
		fileHash=self.hasher(fileName)
		self.Lookup(["LOOKUP_FILE_PUT",fileName,fileHash])



	def get(self, fileName):
		'''
		This function finds node responsible for file given by fileName, gets the file from responsible node, saves it in current directory
		i.e. "./file.py" and returns the name of file. If the file is not present on the network, return None.
		'''
		fileHash=self.hasher(fileName)


		self.Lookup(["LOOKUP_FILE_GET",fileName,fileHash,(self.host,self.port)])

		while self.FileFound==" ":
			pass

		FILE= None if self.FileFound=="None" else self.FileFound
		self.FileFound=" "

		return FILE

		


	def leave(self):
		'''
		When called leave, a node should gracefully leave the network i.e. it should update its predecessor that it is leaving
		it should send its share of file to the new responsible node, close all the threads and leave. You can close listener thread
		by setting self.stop flag to True
		'''

		 
		 
		 

		sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect(self.successor)	
		SendMessage=pickle.dumps(["PRED_UPDATE",self.predecessor])
		 
		sock.send(SendMessage)
		sock.close()
				
		sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect(self.predecessor)	
		SendMessage=pickle.dumps(["SUCC_UPDATE",self.successor,self.secondSuccessor])
		 
		sock.send(SendMessage)
		sock.close()
		
		self.stop=True

		time.sleep(0.5)

		for file in self.files:		#Rehashing files

			File= os.getcwd()+"/"+self.host+"_"+str(self.port)+"/"+file

			sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.connect(self.successor)	#Put file at 
			SendMessage=pickle.dumps(["PUT",file])
			 
			sock.send(SendMessage)
			time.sleep(0.5)
			self.sendFile(sock,File)
			sock.close()

		for file in self.files:
			self.files.remove(file)
			
		for file in self.backUpFiles:
			self.backUpFiles.remove(file)

	def sendFile(self, soc, fileName):
		'''
		Utility function to send a file over a socket
			Arguments:	soc => a socket object
						fileName => file's name including its path e.g. NetCen/PA3/file.py
		'''
		fileSize = os.path.getsize(fileName)
		soc.send(str(fileSize).encode('utf-8'))
		soc.recv(1024).decode('utf-8')
		with open(fileName, "rb") as file:
			contentChunk = file.read(1024)
			while contentChunk!="".encode('utf-8'):
				soc.send(contentChunk)
				contentChunk = file.read(1024)

	def recieveFile(self, soc, fileName):
		'''
		Utility function to recieve a file over a socket
			Arguments:	soc => a socket object
						fileName => file's name including its path e.g. NetCen/PA3/file.py
		'''
		fileSize = int(soc.recv(1024).decode('utf-8'))
		soc.send("ok".encode('utf-8'))
		contentRecieved = 0
		file = open(fileName, "wb")
		while contentRecieved < fileSize:
			contentChunk = soc.recv(1024)
			contentRecieved += len(contentChunk)
			file.write(contentChunk)
		file.close()

	def kill(self):
		# DO NOT EDIT THIS, used for code testing
		self.stop = True

	def Lookup(self, message):

		 

		if message[2]==self.key and message[0]!="JOIN":		#Only true incase in file operations
			if message[0]=="LOOKUP_FILE_PUT":
				sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.connect((self.host,self.port))	#Put file at self
				SendMessage=pickle.dumps(["PUT",message[1]])
				 
				sock.send(SendMessage)
				time.sleep(0.5)
				self.sendFile(sock,message[1])
				sock.close()
			
			else:	#Get
				sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.connect((self.host,self.port))	#Put file at self
				SendMessage=pickle.dumps(["GET",message[1],message[3]]) 	#GET, filename, Address
				sock.send(SendMessage)
				sock.close()

		elif self.key>message[2] and message[2]>self.hasher(self.predecessor[0]+str(self.predecessor[1])):	#Normal case
			
			if (message[0]=="JOIN"):

				self.predecessor=message[1]

				
				sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.connect(message[1])

				SendMessage=pickle.dumps(["JOIN_MULTIPLE_SUCC",(self.host,self.port), self.successor])
				sock.send(SendMessage)
				sock.close()

				time.sleep(0.5)

				delIt=[]
				for file in self.files:
					if self.hasher(file)<=self.hasher(self.predecessor[0]+str(self.predecessor[1])):

						File= os.getcwd()+"/"+self.host+"_"+str(self.port)+"/"+file
						sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
						sock.connect(self.predecessor)	#Put file at 
						SendMessage=pickle.dumps(["PUT",file])
						 
						sock.send(SendMessage)
						time.sleep(0.5)
						self.sendFile(sock,File)
						sock.close()
						delIt.append(file)
				
				for file in delIt:
					 
					 
					 
					 
					self.files.remove(file)


			elif message[0]=="LOOKUP_FILE_PUT":
				sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.connect((self.host,self.port))	#Put file at self
				SendMessage=pickle.dumps(["PUT",message[1]])
				 
				sock.send(SendMessage)
				time.sleep(0.5)
				self.sendFile(sock,message[1])
				sock.close()
			
			else:	#Get
				sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.connect((self.host,self.port))	#Put file at self
				SendMessage=pickle.dumps(["GET",message[1],message[3]]) 	#GET, filename, SocketToSendTo(received in get function)
				sock.send(SendMessage)
				sock.close()


		elif self.key<self.hasher(self.predecessor[0]+str(self.predecessor[1])) and message[2]>self.hasher(self.predecessor[0]+str(self.predecessor[1])):	#first node on circle/ Largest key
			
			if (message[0]=="JOIN"):
				self.predecessor=message[1]

				sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.connect(message[1])

				SendMessage=pickle.dumps(["JOIN_MULTIPLE_SUCC",(self.host,self.port),self.successor])
				sock.send(SendMessage)
				sock.close()

				time.sleep(0.5)

				delIt=[]
				for file in self.files:
					if self.hasher(file)<=self.hasher(self.predecessor[0]+str(self.predecessor[1])):

						File= os.getcwd()+"/"+self.host+"_"+str(self.port)+"/"+file

						sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
						sock.connect(self.predecessor)	#Put file at 
						SendMessage=pickle.dumps(["PUT",file])
						 
						sock.send(SendMessage)
						time.sleep(0.5)
						self.sendFile(sock,File)
						sock.close()
						delIt.append(file)
				
				for file in delIt:				 
					self.files.remove(file)


			elif message[0]=="LOOKUP_FILE_PUT":
				
				sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.connect((self.host,self.port))	#Put file at self
				SendMessage=pickle.dumps(["PUT",message[1]])
				 
				sock.send(SendMessage)
				time.sleep(0.5)
				self.sendFile(sock,message[1])
				sock.close()
			
			else:	#Get
				sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.connect((self.host,self.port))	#Put file at self
				SendMessage=pickle.dumps(["GET",message[1],message[3]]) 	#GET, filename, SocketToSendTo(received in get function)
				sock.send(SendMessage)
				sock.close()

		elif self.key<self.hasher(self.predecessor[0]+str(self.predecessor[1])) and message[2]<self.key:	# Smallest key
			
			if message[0]=="JOIN":
				self.predecessor=message[1]

				sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.connect(message[1])

				SendMessage=pickle.dumps(["JOIN_MULTIPLE_SUCC",(self.host,self.port), self.successor])
				sock.send(SendMessage)
				sock.close()

				time.sleep(0.5)

				delIt=[]
				for file in self.files:
					if self.hasher(file)<=self.hasher(self.predecessor[0]+str(self.predecessor[1])):

						File= os.getcwd()+"/"+self.host+"_"+str(self.port)+"/"+file
						sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
						sock.connect(self.predecessor)	#Put file at 
						SendMessage=pickle.dumps(["PUT",file])
						 
						sock.send(SendMessage)
						time.sleep(0.5)
						self.sendFile(sock,File)
						sock.close()
						delIt.append(file)
				
				for file in delIt:
					 
					 
					 
					 
					self.files.remove(file)


			elif message[0]=="LOOKUP_FILE_PUT":
				sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.connect((self.host,self.port))	#Put file at self
				SendMessage=pickle.dumps(["PUT",message[1]])
				 
				sock.send(SendMessage)
				time.sleep(0.5)
				self.sendFile(sock,message[1])
				sock.close()
			
			else:	#Get
				sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.connect((self.host,self.port))	#Put file at self
				SendMessage=pickle.dumps(["GET",message[1],message[3]]) 	#GET, filename, SocketToSendTo(received in get function)
				sock.send(SendMessage)
				sock.close()

		else:
			sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.connect(self.successor)
			SendMessage=pickle.dumps(["LOOKUP",message])
			sock.send(SendMessage)
			sock.close()


	def Ping(self):
		
		while self.stop==False:
			try:
				if self.successor!=(self.host,self.port):
					sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					sock.connect(self.successor)

					sock.send(pickle.dumps(["PRED_CHECK",(self.host,self.port)]))
					sock.close()

			except:

				self.pingFail=self.pingFail+1
				if self.pingFail==3:	#Node failure

					sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					sock.connect(self.secondSuccessor)	
					SendMessage=pickle.dumps(["PING_FAIL",(self.host,self.port)])
					sock.send(SendMessage)
					sock.close()
					time.sleep(0.5)

					for file in self.backUpFiles:		#Rehashing files
						
						File= os.getcwd()+"/"+self.host+"_"+str(self.port)+"/"+file

						sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
						sock.connect(self.successor)	#Put file at 
						SendMessage=pickle.dumps(["PUT",file])
						sock.send(SendMessage)
						time.sleep(0.5)
						self.sendFile(sock,File)
						sock.close()

			
			time.sleep(0.5)
		

