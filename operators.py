import bpy
import json
import threading
import queue
import socket
from . import encoder

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
    
    def invoke(self,context, event):
        
        #change to active state only if the operator is inactive
        if context.scene.thread_flag == False:
            context.scene.thread_flag = True
            context.scene.modal_flag = True
            self.inqueue = queue.Queue(20)
            self.outqueue = queue.Queue(20)
            listening_thread = threading.Thread(target=self.listener,args=(12345,))
            listening_thread.start()
            wm = context.window_manager
            self._timer = wm.event_timer_add(1.0,context.window)
            #add a modal handler that will allow the plugin to listen for events
            context.window_manager.modal_handler_add(self)
            self.execute(context)
        return {'RUNNING_MODAL'}
    
    def execute(self,context):
        if bpy.context.active_object != None:
            bpy.context.scene.active_obj_name = bpy.context.active_object.name 
        bpy.ops.development.encode_operation()
        print(bpy.context.scene.active_obj_name)
        return {'FINISHED'}
    
    def modal(self,context,event):
        
        #if the modal is no longer active, stop the operation of the thread and finish the operator
        if bpy.context.scene.modal_flag == False:
            bpy.context.scene.thread_flag = False
            return {'FINISHED'}
        
        #if the event matches any of the event types listed, call the execute method
        elif event.type in ('LEFTMOUSE','RIGHTMOUSE','ENTER'):
            pass#self.execute(context)
            
        elif event.type in ('LEFTMOUSE','RIGHTMOUSE','ENTER') and event.value in ('CLICK'):
            pass#self.execute(context)
        
        if event.type == 'TIMER':
           bpy.ops.development.encode_operation()
        
            
        return {'PASS_THROUGH'}
    
    def listener(self,port):
        ''' sets up a server listener'''
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        host = socket.gethostname()
        temp_port = port
        bind_success = False
        while bind_success == False:
            try:
                self.sock.bind((host,temp_port))
                bind_success = True
            except OSError:
                temp_port += 1
                
        self.address = self.sock.getsockname()
        
        while bpy.context.scene.thread_flag == True:
            print("Listening for requests...")
            data,addr = self.sock.recvfrom(4096)
            print(data)
            
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