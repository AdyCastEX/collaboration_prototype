import bpy
import json
import threading
import queue
import socket
import time
import bmesh
from . import encoder
from . import decoder
    
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
    enc      --  an encoder object used to encode an operation 
    last_op  --  a dict object representing the last encoded operation
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
            self.enc = encoder.Encoder()
            self.last_op = {}
            
            #values of the server's ip addr and port are assigned via forms in the plugin's panel
            self.address = self.subscribe((bpy.context.scene.server_ip_address,bpy.context.scene.server_port))
            #bind the listener to the address received from the subscribe function
            self.bind_listener(self.address)
            #create and start the thread for the listener
            listening_thread = threading.Thread(target=self.listener,args=())
            listening_thread.start()
            wm = context.window_manager
            #add an event timer that triggers every n seconds
            self._timer = wm.event_timer_add(1.0,context.window)
            #add a modal handler that will allow the plugin to listen for events
            context.window_manager.modal_handler_add(self)
            self.execute(context)
        return {'RUNNING_MODAL'}
    
    def execute(self,context):
        return {'FINISHED'}
    
    def modal(self,context,event):
        
        #if the modal is no longer active, stop the operation of the thread and finish the operator
        if bpy.context.scene.modal_flag == False:
            self.unbind_listener()
            bpy.context.scene.thread_flag = False
            return {'FINISHED'}
        
        elif event.type in ('LEFTMOUSE','RIGHTMOUSE','ENTER'):
            pass
            
        if event.type in ('TIMER'):
           encode_caller = threading.Thread(target=self.call_encoder(),args=())
           encode_caller.start() 
           op_sender = threading.Thread(target=self.send_operation,args=())
           op_sender.start()
           self.decode_operation()
           
        return {'PASS_THROUGH'}
    
    def bind_listener(self,address):
        ''' sets up a server listener
        
        Parameters
        address -- a tuple containing the ip address and port to bind to
        '''
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        try:
            self.sock.bind(address)
        except OSError:
            pass
        
    def unbind_listener(self):
        '''removes the server listener'''
        self.unsubscribe((bpy.context.scene.server_ip_address,bpy.context.scene.server_port))
        self.sock.close()
        #remove the timer to prevent redundancy when the listener is re-initialized
        bpy.context.window_manager.event_timer_remove(self._timer)
    
    def listener(self):
        '''listens for incoming data from the server'''
        
        #continue the loop only if the thread is clear to run
        while bpy.context.scene.thread_flag == True:
            try:
                print("Listening for requests...")
                data_bytes,addr = self.sock.recvfrom(4096)
                #add the received operation to the in queue if the queue still has space
                if not self.inqueue.full():
                    #convert the byte array (data) to a json string then to a dict
                    data = json.loads(data_bytes.decode('utf-8'))
                    #put the received operation in the in queue
                    self.inqueue.put(data['operation'])
                print(data_bytes)
            except OSError:
                #a sample exception is when the socket is closed while waiting for data
                break
            
    def subscribe(self,server_address):
        '''subscribe to a server's updates
        
        Parameters
        server_address  -- a tuple containing the server's ip address and port
        
        Return Value
        client_address  -- a tuple containing an arbitrary ip address and port assigned by the server
        '''
        s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.connect(server_address)
        request = {
            'action' : 'SUBSCRIBE',
            'ip_addr': '',
            'port' : ''
        }
        
        s.sendall(bytes(json.dumps(request),'utf-8'))
        reply_bytes,addr = s.recvfrom(4096)
        s.close()
        reply = json.loads(reply_bytes.decode('utf-8'))
        client_address = (reply['ip'],reply['port'])
        return client_address
    
    def unsubscribe(self,server_address):
        ''' unsubscribe from a server's updates
        
        Parameters
        server_address -- a tuple containing the server's ip address and port
        
        '''
        s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.connect(server_address)
        request = {
            'action' : 'UNSUBSCRIBE',
            'ip_addr' : self.address[0],
            'port' : self.address[1]
        }
        
        s.sendall(bytes(json.dumps(request),'utf-8'))
        reply_bytes,addr = s.recvfrom(4096)
        s.close()
        
    def encode_operation(self):
        ''' gets an operator from the operator history and encodes it into sendable form'''
        #attempt to get an operator only if the operators list is not empty
        if len(bpy.context.window_manager.operators) > 0:
            #get the last executed operator
            latest_op = bpy.context.active_operator
            #latest_op = bpy.context.window_manager.operators[-1]
            
            #check first if the opeation has not been encoded before to prevent unnecessary doubling
            if latest_op != self.last_op:
                #if the operation is different from the last one, update the last operation
                self.last_op = latest_op
                try:
                    #get the method that matches the name of the last operator
                    encode_function = getattr(self.enc,self.enc.format_op_name(latest_op.name))
                    mode = bpy.context.mode
                    selected = {
                        'objects' : self.enc.get_obj_names(bpy.context.selected_objects)
                    }
                    if bpy.context.active_object != None:
                        active_object = bpy.context.active_object.name
                        if mode in ('EDIT_MESH'):
                            internals = self.get_internals(bpy.context.active_object)
                            selected['verts'] = internals['verts']
                            selected['edges'] = internals['edges']
                            selected['faces'] = internals['faces']
                    else:
                        active_object = ''
                    
                    #execute the method to get an encoded operation
                    operation = encode_function(latest_op,selected,active_object,mode)
                    if not self.outqueue.full():
                        self.outqueue.put(operation)
                    print(operation)
                except AttributeError:
                    print("operation not supported")
        
    def call_encoder(self):
        if bpy.context.selected_objects != []:
            selected_objects = self.enc.get_obj_names(bpy.context.selected_objects)
            bpy.context.scene.active_obj_name = json.dumps(selected_objects) 
        self.encode_operation()
        #print(bpy.context.scene.active_obj_name)
            
    def decode_operation(self):
        '''gets an operation from a queue and calls the appropriate function '''
        #print("decode")
        if not self.inqueue.empty():
            op = self.inqueue.get()
            decode_function = getattr(self.dec,self.dec.format_op_name(op['name']))
            decode_function(op)
            
    def send_operation(self):
        '''gets an operation from the outqueue and sends it to the server'''
        #send an operation only if the out queue is not empty
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
        
    def get_internals(self,active_object):
        '''gets the set of selected vertices, edges and faces
        
        Parameters
        active_object     -- a string containing the name of the object that contains the internals
        
        Return Value
        internals         -- a dictionary object that contains the following:
            verts         -- a list containing the indices of selected vertices
            edges         -- a list containing the indices of selected edges
            faces         -- a list containing the indices of selected faces
        
        '''
        bm = bmesh.from_edit_mesh(active_object.data)
        
        verts = [i.index for i in bm.verts if i.select]
        edges = [i.index for i in bm.edges if i.select]
        faces = [i.index for i in bm.faces if i.select]
        
        internals = {
            'verts' : verts,
            'edges' : edges,
            'faces' : faces
        }
        
        return internals
            
            
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
        