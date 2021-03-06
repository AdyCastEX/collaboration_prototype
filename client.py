import bpy
import json
import threading
import queue
import socket
import time
from . import encoder
from . import decoder
from . import utils
    
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
            
            #values of the server's ip addr and port are assigned via forms in the plugin's panel
            result = self.subscribe((bpy.context.scene.server_ip_address,bpy.context.scene.server_port))
            
            #activate plugin functionality only if the subscription was successful
            if result['success'] == True:
                
                #initialize flags and storage objects
                context.scene.thread_flag = True
                context.scene.modal_flag = True
                self.inqueue = queue.Queue(20)
                self.outqueue = queue.Queue(20)
                self.dec = decoder.Decoder()
                self.enc = encoder.Encoder()
                self.last_op = {}
                
                
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
                
            else:
                pass
        return {'RUNNING_MODAL'}
    
    def execute(self,context):
        return {'FINISHED'}
    
    def modal(self,context,event):
        
        #if the modal is no longer active, stop the operation of the thread and finish the operator
        if bpy.context.scene.modal_flag == False:
            self.unbind_listener()
            bpy.context.scene.thread_flag = False
            #get the last operator and encode it using the appropriate encode function
            last_op = bpy.context.active_operator
            if last_op != None:
                try:
                    encode_function = getattr(self.enc,utils.format_op_name(last_op.name))
                    empty_targets = {'objects':[],'verts':[],'edges':[],'faces':[],'select_mode':''}
                    bpy.context.scene.last_op = json.dumps(encode_function(last_op,empty_targets,'',bpy.context.mode))
                except AttributeError:
                    print("operation not supported")
            #reset the encode flag to false
            bpy.context.scene.encode_flag = False
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
        result           -- a dict object containing the following:
            success      -- a boolean value indicating whether the subscription succeeeded or not (True or False)
            ip_addr      -- an arbitrary ip address string assigned by the server
            port         -- an arbitrary port number assigned by the server
        '''
        try:
            s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            s.connect(server_address)
            request = {
                'action' : 'SUBSCRIBE',
                'ip_addr': '',
                'port' : '',
                'filename' : bpy.context.scene.session_name
            }
            
            #send a request to register the user to the list of clients in the server
            s.sendall(bytes(json.dumps(request),'utf-8'))
            s.settimeout(5.0)
        
            #wait for an acknowledgement from the server
            reply_bytes = s.recv(4096)
            s.close()
            reply = json.loads(reply_bytes.decode('utf-8'))
            print(reply)
            
            result = {
                'success' : reply['success'],
                'ip_addr' : reply['ip'],
                'port'    : reply['port']
                      
            }
            
            if reply['success'] == True:
                self.address = (result['ip_addr'],result['port'])
                self.request_file(server_address)
                utils.load_state(bpy.context.scene.client_filepath,bpy.context.scene.session_name)
                #utils.format_obj_names("_",".")
                
        except TimeoutError:
            result = {
                'success' : False,
                'ip_addr' : '',
                'port' : ''
            }
            print("Connection timed out!")
            self.report('ERROR',"Connection timed out!")
            
        except ConnectionRefusedError:
            result = {
                'success' : False,
                'ip_addr' : '',
                'port' : ''
            }
            print("Connection refused!")
            
        
        return result
    
    def unsubscribe(self,server_address):
        ''' unsubscribe from a server's updates
        
        Parameters
        server_address -- a tuple containing the server's ip address and port
        
        '''
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            s.connect(server_address)
            request = {
                'action' : 'UNSUBSCRIBE',
                'ip_addr' : self.address[0],
                'port' : self.address[1]
            }
            s.settimeout(5.0)
            s.sendall(bytes(json.dumps(request),'utf-8'))
            reply_bytes = s.recv(4096)
        except TimeoutError:
            print("Connection timed out!")
        except ConnectionRefusedError:
            print("Connection refused!")
        s.close()
        
    def request_file(self,server_address):
        '''request a collada file from the server
        
        Parameters
        server_address     -- a tuple containing the ip address and port of the server to connect to
        '''
        
        requester = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        requester.connect(server_address)
        
        request = {
            'action' : 'REQUEST_FILE',
            'ip_addr' : self.address[0],
            'port' : self.address[1],
            'filename' : bpy.context.scene.session_name
        }
        
        #send a request for the specified file
        requester.sendall(bytes(json.dumps(request),'utf-8'))
        
        #filepath -- the folder where the file will be saved once received
        filepath = bpy.context.scene.client_filepath
        #if the directory/folder does not exist, create it
        if not utils.check_dir(filepath):
            utils.create_directory(filepath)
        
        filename = filepath + "/" + bpy.context.scene.session_name + ".dae"
        #open the file for writing in binary
        output_file = open(filename,'wb')
        
        #receive a fragment of the file
        server_reply = requester.recv(4096)
        #keep waiting for fragments while the file is not complete
        while server_reply:
            #print(server_reply)
            #print("end of frame")
            #write the received bytes to the output file
            output_file.write(server_reply)
            server_reply = requester.recv(4096)
            
        #close the file stream
        output_file.close()
        requester.close()
            
        
    def encode_operation(self):
        ''' gets an operator from the operator history and encodes it into sendable form'''
        #attempt to get an operator only if the operators list is not empty
        if len(bpy.context.window_manager.operators) > 0:
            #get the last executed operator
            latest_op = bpy.context.active_operator
            #latest_op = bpy.context.window_manager.operators[-1]
            
            #check if the encoder is clear to encode
            if bpy.context.scene.encode_flag == True:
                #check first if the opeation has not been encoded before to prevent unnecessary doubling
                if latest_op != self.last_op:
                    #if the operation is different from the last one, update the last operation
                    self.last_op = latest_op
                    try:
                        #utils.format_obj_names(".","_")
                        #get the method that matches the name of the last operator
                        encode_function = getattr(self.enc,utils.format_op_name(latest_op.name))
                        mode = bpy.context.mode
                        selected = {}
                        if bpy.context.selected_objects != []:
                            selected['objects'] = utils.get_obj_names(bpy.context.selected_objects)
                        
                        if bpy.context.active_object != None:
                            active_object = bpy.context.active_object.name
                            if mode in ('EDIT_MESH'):
                                select_mode = utils.get_select_mode()
                                internals = utils.get_internals(bpy.context.active_object.name,select_mode)
                                selected['verts'] = internals['verts']
                                selected['edges'] = internals['edges']
                                selected['faces'] = internals['faces']
                                selected['select_mode'] = select_mode
                        else:
                            active_object = ''
                        
                        #execute the method to get an encoded operation
                        operation = encode_function(latest_op,selected,active_object,mode)
                        if not self.outqueue.full():
                            self.outqueue.put(operation)
                            #bpy.context.scene.last_op = json.dumps(operation)
                        print(operation)
                    except AttributeError:
                        print("operation not supported")
                        
            #if the enoder is not clear to encode, check for clear condition
            elif bpy.context.scene.encode_flag == False:
                
                try:
                    #if there was a last operation (string form), convert to dict
                    last_op = json.loads(bpy.context.scene.last_op)
                except ValueError:
                    #if there was no last operation, just set to empty dict since json cannot decode empty strings
                    last_op = {}
                
                try:
                    #get the current active operator and encode using the appropriate encode function
                    curr_op = bpy.context.active_operator
                    encode_function = getattr(self.enc,utils.format_op_name(curr_op.name))
                    empty_targets = {'objects':[],'verts':[],'edges':[],'faces':[],'select_mode':''}
                    #to prevent unncessary encodes when a user rejoins a session, set the encode flag to true only when a new operation is added
                    if not utils.op_equivalent(last_op,encode_function(curr_op,empty_targets,'',bpy.context.mode)):
                        bpy.context.scene.encode_flag = True
                except AttributeError:
                    pass
        
    def call_encoder(self):
        '''keeps track of selected objects/internals (mostly for backtracking in delete) and calls the encoder'''
        if bpy.context.selected_objects != []:
            selected_objects = utils.get_obj_names(bpy.context.selected_objects)
            bpy.context.scene.active_obj_name = json.dumps(selected_objects)
            if bpy.context.mode in ('EDIT_MESH'):
                selected_internals = utils.get_internals(bpy.context.active_object.name,utils.get_select_mode())
                #update the last selected internals only if not empty to avoid select mismatches on delete
                if selected_internals['verts'] != [] or selected_internals['edges'] != [] or selected_internals['faces'] != []:
                    bpy.context.scene.selected_internals = json.dumps(selected_internals)
                #print(bpy.context.scene.selected_internals) 
        self.encode_operation()
        #print(bpy.context.scene.active_obj_name)
        
            
    def decode_operation(self):
        '''gets an operation from a queue and calls the appropriate function '''
        #print("decode")
        if not self.inqueue.empty():
            op = self.inqueue.get()
            decode_function = getattr(self.dec,utils.format_op_name(op['name']))
            decode_function(op)
            #utils.format_obj_names(".","_")
            
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
        