import bpy
import json
import threading
import queue
import socket
from . import encoder
from . import decoder

class StartServer(bpy.types.Operator):
    '''starts a persistent collaboration server'''
    bl_idname = "development.start_server"
    bl_label = "Start Server"
    bl_description = "Starts a persistent collaboration server"
    
    ''' 
    Attributes
    servsock    -- a socket object used to serve requests
    clients     -- a list containing the addresses of the clients
    address     -- a tuple containing the ip address and port of the server socket
    dec         -- a decoder object used to run operations
    '''
    
    def invoke(self,context, event):
        
        if bpy.context.scene.thread_flag == False:
            
            #set flags to true 
            bpy.context.scene.thread_flag = True
            bpy.context.scene.modal_flag = True
            
            #attribute initializations
            self.clients = []
            self.dec = decoder.Decoder()
            
            #initialize the server
            self.init_server(5050)
            serverthread = threading.Thread(target=self.server_thread,args=())
            serverthread.start()
            
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
            print("timer")
        return {'PASS_THROUGH'}
    
    def init_server(self,port):
        '''initialize a server 
        
        Parameters
        port  -- the port number of the server
        
        '''
        
        self.servsock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        host = socket.gethostname()
        temp_port = port
        success_flag = False
        while success_flag == False:
            try:
                self.servsock.bind((host,temp_port))
                success_flag = True
            except OSError:
                temp_port+=1
                
        self.addr = self.servsock.getsockname()
        
    def close_server(self):
        ''' close a server '''
        self.servsock.close()
        #remove the timer to prevent redundancy when the server is re-initialized
        bpy.context.window_manager.event_timer_remove(self._timer)
    
    def server_thread(self):
        
        while bpy.context.scene.thread_flag == True:
            
            try:
                print("Listening for requests...")
                data, addr = self.servsock.recvfrom(4096)
                #convert the bytes object into a dictionary object
                data_json = json.loads(data.decode())
                sender = (data_json['ip_addr'],data_json['port'])
                action = data_json['action']
                #add a new subscriber if not yet in the list 
                if sender not in self.clients and action in ('LOGIN','SUBSCRIBE'):
                    t = threading.Thread(target=self.subscribe_thread,args=(sender,addr))
                    t.start()
                
                #if the received data is a sent operation
                if action in ('SEND'):
                    t = threading.Thread(target=self.client_thread,args=(data,sender))
                    t.start()
            except OSError:
                #this can happen when the socket is suddenly closed while waiting for data
                break
    
    
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
            
    def subscribe_thread(self,sender,addr):
        '''add a node to the list of clients and return an acknowledgement of success
        
        Parameters
        sender  -- a tuple containing the ip address and port data of a node
        addr    -- the address of the socket used to send a subscribe request
        '''
        
        self.clients.append(sender)
        print(self.clients)
        ack = {
            'success' : True
        }
        #convert the ack dict into a json string then encode as a bytes object before sending
        self.servsock.sendto(bytes(json.dumps(ack),'utf-8'),addr)
        
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
    
    