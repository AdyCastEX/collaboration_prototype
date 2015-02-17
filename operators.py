import bpy
import json
import threading
import queue
import socket
from . import encoder
from . import decoder

class EncodeOperation(bpy.types.Operator):
    '''gets the last executed operator and encodes it for sending'''
    bl_idname = "development.encode_operation"
    bl_label = "Encode Opeation"
    bl_description = "Gets the last executed operator and encodes it for sending"
    
    def invoke(self,context,event):
        return self.execute(context)
    
    def execute(self,context):
        
        #attempt to get an operator only if the operators list is not empty
        if len(bpy.context.window_manager.operators) > 0:
            #get the last executed operator
            latest_op = bpy.context.window_manager.operators[-1]
            try:
                enc = encoder.Encoder()
                #get the method that matches the name of the last operator
                encode_function = getattr(enc,enc.format_op_name(latest_op.name))
                active_object = bpy.context.active_object
                mode = bpy.context.mode
                #execute the method to get an encoded operation
                operation = encode_function(latest_op,active_object,mode)
                print(operation)
            except AttributeError:
                print("encode error")
        return {'FINISHED'}
        
    
class StartSession(bpy.types.Operator):
    ''' initiates a persistent collaborative session ''' 
    
    bl_idname = "development.start_session"
    bl_label = "Start Session"
    bl_description = "Initiates a persistent collaborative session"
    
    '''
    Attributes
    inqueue  --  a queue object used as temporary storage for incoming operations
    outqueue --  a queue object used as temporary storage for outgoing operations
    sock     --  a socket object used to listen to the server
    address  --  a tuple containing the ip address and port of the socket listener
    dec      --  a decoder object used to decode and execute a received operation
    '''
    def invoke(self,context, event):
        
        #change to active state only if the operator is inactive
        if context.scene.thread_flag == False:
            #initialize flags and storage objects
            context.scene.thread_flag = True
            context.scene.modal_flag = True
            self.inqueue = queue.Queue(20)
            self.outqueue = queue.Queue(20)
            self.dec = decoder.Decoder()
            
            #attempt bind the listener socket starting from the specified port 
            self.bind_listener(12345)
            #create start the thread for the listener
            listening_thread = threading.Thread(target=self.listener,args=())
            listening_thread.start()
            #values of the server's ip addr and port are assigned via forms in the plugin's panel
            self.subscribe((bpy.context.scene.server_ip_address,bpy.context.scene.server_port))
            
            wm = context.window_manager
            #add an event timer that triggers every n seconds
            self._timer = wm.event_timer_add(1.0,context.window)
            #add a modal handler that will allow the plugin to listen for events
            context.window_manager.modal_handler_add(self)
            self.execute(context)
        return {'RUNNING_MODAL'}
    
    def execute(self,context):
        if bpy.context.active_object != None:
            bpy.context.scene.active_obj_name = bpy.context.active_object.name 
        self.encode_operation()
        print(bpy.context.scene.active_obj_name)
        return {'FINISHED'}
    
    def modal(self,context,event):
        
        #if the modal is no longer active, stop the operation of the thread and finish the operator
        if bpy.context.scene.modal_flag == False:
            self.unbind_listener()
            bpy.context.scene.thread_flag = False
            return {'FINISHED'}
        
        #if the event matches any of the event types listed, call the execute method
        elif event.type in ('LEFTMOUSE','RIGHTMOUSE','ENTER'):
            self.execute(context)
            
        elif event.type in ('LEFTMOUSE','RIGHTMOUSE','ENTER') and event.value in ('CLICK'):
            pass#self.execute(context)
        
        if event.type in ('TIMER'):
           self.decode_operation()
           self.send_operation()
        return {'PASS_THROUGH'}
    
    def bind_listener(self,port):
        ''' sets up a server listener
        
        Parameters
        port -- the port number of the listener
        '''
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        #dynamically get the hostname of the machine
        host = socket.gethostname()
        temp_port = port
        bind_success = False
        #attempt to bind the socket to a specific port until a free port is found
        while bind_success == False:
            try:
                self.sock.bind((host,temp_port))
                bind_success = True
            except OSError:
                #if the port is taken, check the next one
                temp_port += 1
                
        #set the address which is a tuple containing the ip address and port of the socket
        self.address = self.sock.getsockname()
        
    def unbind_listener(self):
        '''removes the server listener'''
        self.sock.close()
        #remove the timer to prevent redundancy when the listener is re-initialized
        bpy.context.window_manager.event_timer_remove(self._timer)
    
    def listener(self):
        '''listens for incoming data from the server'''
        
        #continue the loop only if the thread is clear to run
        while bpy.context.scene.thread_flag == True:
            try:
                print("Listening for requests...")
                data,addr = self.sock.recvfrom(4096)
                print(data)
            except OSError:
                #a sample exception is when the socket is closed while waiting for data
                break
            
    def subscribe(self,server_address):
        '''subscribe to a server's updates
        
        Parameters
        server_address  -- a tuple containing the server's ip address and port
        '''
        s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.connect(server_address)
        request = {
            'action' : 'SUBSCRIBE',
            'ip_addr' : self.address[0],
            'port' : self.address[1]
        }
        
        s.sendall(bytes(json.dumps(request),'utf-8'))
        reply,addr = s.recvfrom(4096)
        s.close()
            
    def encode_operation(self):
        ''' gets an operator from the operator history and encodes it into sendable form'''
        #attempt to get an operator only if the operators list is not empty
        if len(bpy.context.window_manager.operators) > 0:
            #get the last executed operator
            latest_op = bpy.context.window_manager.operators[-1]
            try:
                enc = encoder.Encoder()
                #get the method that matches the name of the last operator
                encode_function = getattr(enc,enc.format_op_name(latest_op.name))
                active_object = bpy.context.active_object
                mode = bpy.context.mode
                #execute the method to get an encoded operation
                operation = encode_function(latest_op,active_object,mode)
                if not self.outqueue.full():
                    self.outqueue.put(operation)
                print(operation)
            except AttributeError:
                print("encode error")
        
            
    def decode_operation(self):
        '''gets an operation from a queue and calls the appropriate function '''
        print("decode")
        if not self.inqueue.empty():
            op = self.inqueue.get()
            decode_function = getattr(self.dec,self.dec.format_op_name(op['name']))
            decode_function(op)
            
    def send_operation(self):
        '''gets an operation from the outqueue and sends it to the server'''
        if not self.outqueue.empty():
            s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            s.connect((bpy.context.scene.server_ip_address,bpy.context.scene.server_port))
            op = self.outqueue.get()
            
            data = {
                'action' : 'SEND',
                'ip_addr' : self.address[0],
                'port' : self.address[1],
                'operation' : op        
            }
            
            s.sendall(bytes(json.dumps(data),'utf-8'))
            s.close()
        
            
class EndSession(bpy.types.Operator):
    ''' ends a persistent collaborative session '''
    bl_idname = "development.end_session"
    bl_label = "End Session"
    bl_description = "Ends a persistent collaborative session"
    
    def invoke(self,context, event):
        return self.execute(context)

    def execute(self,context):
        bpy.context.scene.modal_flag = False
        return {'FINISHED'}
        
class SendOperation(bpy.types.Operator):
    '''sends an operation to a server'''
    bl_idname = "development.send_operation"
    bl_label = "Send Operation"
    bl_description = "Sends an operation to a server"
    
    def invoke(self,context, event):
        return self.execute(context)
    
    def execute(self,context):
        return {'FINISHED'}