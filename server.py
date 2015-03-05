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
    servsock    -- a socket object used to serve requests
    clients     -- a list containing the addresses of the clients
    address     -- a tuple containing the ip address and port of the server socket
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
        #host = socket.gethostname()
        temp_port = port
        success_flag = False
        while success_flag == False:
            try:
                self.servsock.bind(('',temp_port))
                print(temp_port)
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
                data_bytes, addr = self.servsock.recvfrom(4096)
                #convert the bytes object into a dictionary object
                data = json.loads(data_bytes.decode())
                sender = (data['ip_addr'],data['port'])
                action = data['action']
                #add a new subscriber if not yet in the list of clients
                if addr not in self.clients and action in ('LOGIN','SUBSCRIBE'):
                    t = threading.Thread(target=self.subscribe_thread,args=('',addr))
                    t.start()
                
                #accept data if it came from a node in the list of clients and that client intends to send data
                elif sender in self.clients and action in ('SEND'):
                    if not self.inqueue.full():
                        self.inqueue.put(data)
                        
                elif sender in self.clients and action in ('LOGOUT','UNSUBSCRIBE'):
                    t = threading.Thread(target=self.unsubscribe_thread,args=(sender,addr))
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
        
        self.clients.append(addr)
        print(self.clients)
        ack = {
            'success' : True,
            'ip' : addr[0],
            'port' : addr[1]
        }
        #convert the ack dict into a json string then encode as a bytes object before sending
        self.servsock.sendto(bytes(json.dumps(ack),'utf-8'),addr)
        
    def unsubscribe_thread(self,sender,addr):
        '''remove a node from the list of clients
        
        sender  -- a tuple containing the ip address and port data of a node
        addr    -- a tuple containing the ip address and port data of the socket that sent the request
        '''
        
        self.clients.remove(sender)
        print(self.clients)
        ack = {
            'success' : True
        }
        
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
        
    def process_operation(self):
        '''performs the necessary processing of an operation on the server's instance of the collaborative session'''
        if not self.inqueue.empty():
            data = self.inqueue.get()
            op = data['operation']
            
            #Operational Transformation goes here
            
            self.execute_operation(op)
            data['operation'] = op
            
            self.save_state()
            
            if not self.outqueue.full():
                self.outqueue.put(data)
        
    def execute_operation(self,op):
        ''' execute the operation on the server's instance of the collaborative session
        
        Parameters
        op      -- the operation for execution, in dictionary format
        
        '''
        op_function = getattr(self.dec,self.dec.format_op_name(op['name']))
        op_function(op)
        
    def broadcast_operation(self):
        '''gets an operation from the outqueue and starts a thread for sending data to connected clients'''
        if not self.outqueue.empty():
            data_json = self.outqueue.get()
            sender = (data_json['ip_addr'],data_json['port'])
            data = bytes(json.dumps(data_json),'utf-8')
            t = threading.Thread(target=self.client_thread,args=(data,sender))
            t.start()
            
    def save_state(self):
        ''' exports the current state of the scene to a collada (.dae) file '''
        
        
        filepath = bpy.context.scene.server_filepath
        
        if not os.path.isdir(filepath):
            utils.create_directory(filepath) 
        filename = filepath + "/" + bpy.context.scene.session_name
        
        bpy.ops.wm.collada_export(filepath=filename)
            
            
        
            
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
    
    