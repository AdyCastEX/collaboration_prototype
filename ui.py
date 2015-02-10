import bpy

class CollaborationPanel(bpy.types.Panel):
    
    bl_idname = "OBJECT_PT_collaboration"
    bl_label = "Collaboration"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    
    def draw(self,context):
        layout = self.layout
        
        row = layout.row()
        row.operator("development.start_session")
        row = layout.row()
        row.operator("development.end_session")