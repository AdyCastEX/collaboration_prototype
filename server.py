import bpy
import json
import threading
import queue
import socket
import os
from . import encoder
from . import decoder
from . import utils

class StartServer(bpy.types.Operator):
    '''starts a persistent collaboration server'''
    bl_idname = "development.start_server"
    bl_label = "Start Server"
    bl_description = "Starts a persistent collaboration server"
    
    ''' 
    Attributes
    servsock    -- a UDP socket object used to serve requests
    regsock    -- a TCP socket object used for subscription and sending files
    clients     -- a list containing the addresses of the clients
    addr        -- a tuple containing the ip address and port of the server socket
    dec         -- a decoder object used to run operations
    inqueue     -- a Queue object that stores received operations
    outqueue    -- a Queue object that stores operations to send to clients
    '''
    
    def invoke(self,context, event):
        
        if bpy.context.scene.thread_flag == False:
            
            #set flags to true 
            bpy.context.scene.thread_flag = True
            bpy.context.scene.modal_flag = True
            
            #attribute initializations
            self.clients = []
            self.dec = decoder.Decoder()
            self.inqueue = queue.Queue(30)
            self.outqueue = queue.Queue(30)
            
            load_flag = utils.load_state(bpy.context.scene.server_filepath,bpy.context.scene.session_name)
            if not load_flag:
                utils.save_state(bpy.context.scene.server_filepath,bpy.context.scene.session_name)
            
            #initialize the server
            self.init_server(5050)
            serverthread = threading.Thread(target=self.server_thread,args=())
            serverthread.start()
            registerthread = threading.Thread(target=self.register_thread,args=())
            registerthread.start()
            
            #bind the modal events
            self._timer = bpy.context.window_manager.event_timer_add(1.0, context.window)
            bpy.context.window_manager.modal_handler_add(self)
            
        return {'RUNNING_MODAL'}
    
    def execute(self,context):
        return {'FINISHED'}
    
    def modal(self,context, event):
        #if the modal is no longer active, stop the operation of the thread and finish the operator
        if bpy.context.scene.modal_flag == False:
            self.close_server()
            bpy.context.scene.thread_flag = False
            return {'FINISHED'}
        
        if event.type in ('TIMER'):
            #print("timer")
            self.process_operation()
            self.broadcast_operation()
            
        return {'PASS_THROUGH'}
    
    def init_server(self,port):
        '''initialize a server 
        
        Parameters
        port  -- the port number of the server
        
        '''
        
        self.servsock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.regsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        #host = socket.gethostname()
        temp_port = port
        success_flag = False
        while success_flag == False:
            try:
                self.servsock.bind(('',temp_port))
                self.regsock.bind(('',temp_port))
                self.regsock.listen(10)
                print(temp_port)
                success_flag = True
            except OSError:
                temp_port+=1        
        self.addr = self.servsock.getsockname()
        
    def close_server(self):
        ''' close a server '''
        self.servsock.close()
        self.regsock.close()
        #remove the timer to prevent redundancy when the server is re-initialized
        bpy.context.window_manager.event_timer_remove(self._timer)
    
    def server_thread(self):
        
        while bpy.context.scene.thread_flag == True:
            
            try:
                print("Listening for requests...")
                data_bytes, addr = self.servsock.recvfrom(4096)
                #convert the bytes object into a dictionary object
                data = json.loads(data_bytes.decode())
                sender = (data['ip_addr'],data['port'])
                action = data['action']
                
                #accept data if it came from a node in the list of clients and that client intends to send data
                if sender in self.clients and action in ('SEND'):
                    if not self.inqueue.full():
                        self.inqueue.put(data)
                                            
            except OSError:
                #this can happen when the socket is suddenly closed while waiting for data
                break
            
    def register_thread(self):
        '''a thread function that continuously listens for login or logout requests'''
        while bpy.context.scene.thread_flag == True:
            try:
                conn,addr = self.regsock.accept()
                
                data_bytes = conn.recv(4096)
                data = json.loads(data_bytes.decode('utf-8'))
                sender = (data['ip_addr'],data['port'])
                action = data['action']
                print(data_bytes)
                
                #add a new subscriber if not yet in the list of clients
                if addr not in self.clients and action in ('LOGIN','SUBSCRIBE'):
                    t = threading.Thread(target=self.subscribe_thread(conn, addr, data))
                    t.start()
                
                elif sender in self.clients and action in ('LOGOUT','UNSUBSCRIBE'):
                    t = threading.Thread(target=self.unsubscribe_thread(sender, conn))
                    t.start()
                    
                elif sender in self.clients and action in ('REQUEST_FILE'):
                    t = threading.Thread(target=self.send_file,args=(conn,data))
                    t.start()
                
            except OSError:
                pass
    
    def client_thread(self,data,sender):
        ''' broadcasts data to all connected clients except for the sender
        
        Parameters
        data -- the data to send in bytes format
        sender -- a tuple containing the ip address and port of the sender
        '''
        
        print(data)
        for client in self.clients:
            #no need to send data to the node that sent the data
            if client == sender:
                continue
            
            self.send_data(data,client)
            
    def subscribe_thread(self,sender,addr,data):
        '''add a node to the list of clients and return an acknowledgement of success
        
        Parameters
        sender  -- a TCP socket object used to send data back to a node
        addr    -- the address of the socket that sent a request
        data    -- a dict object that contains data received from a node
        '''
        
        #if the requested file/session exists, add the user to the list of clients and send a success acknowledgement
        if utils.check_file(bpy.context.scene.server_filepath,data['filename']):
            self.clients.append(addr)
            print(self.clients)
            ack = {
                'success' : True,
                'ip' : addr[0],
                'port' : addr[1]
            }
            
        #if the requested file/session does not exist, do not add the user to the list and send a failure acknowledgement
        elif not utils.check_file(bpy.context.scene.server_filepath,data['filename']):
            print(self.clients)
            ack = {
                'success' : False,
                'ip' : addr[0],
                'port' : addr[1]
            }
        #convert the ack dict into a json string then encode as a bytes object before sending
        sender.sendall(bytes(json.dumps(ack),'utf-8'))
        
    def unsubscribe_thread(self,sender,conn):
        '''remove a node from the list of clients
        
        sender  -- a tuple containing the ip address and port data of a node
        conn    -- a TCP socket object used to communicate with a sender
        '''
        
        self.clients.remove(sender)
        print(self.clients)
        ack = {
            'success' : True
        }
        
        conn.sendall(bytes(json.dumps(ack),'utf-8'))
        
    def send_file(self,conn,data):
        '''sends a file to a client
        
        Parameters

        conn      -- a TCP socket object used to connect to a client
        data      -- a dictionary object that contains information from a client
        
        '''
        
        filename = bpy.context.scene.server_filepath + "/" + data['filename'] + ".dae"
        
        try:
            #open the collada file for reading in binary mode
            reply_file = open(filename,'rb')
            #get a fragment (4096 bytes) of the file
            file_part = reply_file.read(4096)
            #keep getting fragments and send them as long as there are still bytes to read
            while file_part:
                print('sending part...')
                conn.sendall(file_part)
                file_part = reply_file.read(4096)
        except IOError:
            print("File not found")
            
        conn.close()
        
    def send_data(self,data,receiver):
        '''send data to a specific receiver
        
        Parameters
        data -- the data to send in bytes format
        receiver -- a tuple containing the ip address and port of the receiving end
        '''
    
        s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.connect(receiver)
        s.sendto(data,receiver)
        s.close()
        
    def process_operation(self):
        '''performs the necessary processing of an operation on the server's instance of the collaborative session'''
        if not self.inqueue.empty():
            data = self.inqueue.get()
            op = data['operation']
            
            #Operational Transformation goes here
            
            self.execute_operation(op)
            data['operation'] = op
            
            utils.save_state(bpy.context.scene.server_filepath,bpy.context.scene.session_name)
            
            if not self.outqueue.full():
                self.outqueue.put(data)
        
    def execute_operation(self,op):
        ''' execute the operation on the server's instance of the collaborative session
        
        Parameters
        op      -- the operation for execution, in dictionary format
        
        '''
        op_function = getattr(self.dec,utils.format_op_name(op['name']))
        op_function(op)
        
    def broadcast_operation(self):
        '''gets an operation from the outqueue and starts a thread for sending data to connected clients
        
        '''
        if not self.outqueue.empty():
            data_json = self.outqueue.get()
            sender = (data_json['ip_addr'],data_json['port'])
            data = bytes(json.dumps(data_json),'utf-8')
            t = threading.Thread(target=self.client_thread,args=(data,sender))
            t.start()
            
    
                
class StopServer(bpy.types.Operator):
    '''stops a collaboration server '''
    bl_idname = "development.stop_server"
    bl_label = "Stop Server"
    bl_description = "Stops a collaboration server"
    
    def invoke(self,context, event):
        return self.execute(context)
    
    def execute(self,context):
        bpy.context.scene.modal_flag = False
        return {'FINISHED'}
    
    