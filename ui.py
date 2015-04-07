import bpy
import socket

class CollaborationPanel(bpy.types.Panel):
    
    bl_idname = "OBJECT_PT_collaboration"
    bl_label = "Collaboration"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    
    def draw(self,context):
        layout = self.layout
        sceneprops = bpy.context.scene
        
        # "Tabs" used to separate the client mode from server mode
        layout.prop(sceneprops,"mode",expand=True)
        
        if sceneprops.mode == "CLIENT":
            row = layout.row()
            row.label(text="STATUS : ")
            if bpy.context.scene.modal_flag == True:
                row.label(text="ONLINE")
            elif bpy.context.scene.modal_flag == False:
                row.label(text="OFFLINE")
            row = layout.row()
            row.prop(sceneprops,"client_filepath",text='Filepath')
            row = layout.row()
            row.prop(sceneprops,"session_name",text="Session")
            row = layout.row()
            #a text field that updates bpy.context.scene.server_ip_address
            row.prop(bpy.context.scene,"server_ip_address",text="IP Address")
            row = layout.row()
            #a number field that updates bpy.context.scene.server_port 
            row.prop(bpy.context.scene,"server_port",text="Port")
            row = layout.row()
            #a button that calls bpy.ops.development.start_session()
            row.operator("development.start_session")
            row = layout.row()
            #a button that calls bpy.ops.development.end_session()
            row.operator("development.end_session")
            
            
        elif sceneprops.mode == "SERVER":
            row = layout.row()
            row.label(text="STATUS : ")
            if bpy.context.scene.modal_flag == True:
                row.label(text="ONLINE")
            elif bpy.context.scene.modal_flag == False:
                row.label(text="OFFLINE")
            row = layout.row()
            row.label(text="PORT : ")
            row.label(text=str(bpy.context.scene.server_port))
            row = layout.row()
            row.prop(sceneprops,"session_name",text="Session")
            row = layout.row()
            row.prop(sceneprops,"server_filepath",text="Filepath")
            row = layout.row()
            #a button that calls bpy.ops.development.start_server()
            row.operator("development.start_server")
            row = layout.row()
            #a button that calls bpy.ops.development.stop_server()
            row.operator("development.stop_server")
        
        