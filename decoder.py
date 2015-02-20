import bpy

class Decoder:
    
    def format_op_name(self,op_name):
        '''converts an operator name to a format that follows method naming conventions
        
        Parameters:
        op_name -- the name of the operator from the info space
        
        '''
        #convert the op name to lowercase
        formatted_name = op_name.lower()
        #replace all spaces with underscores
        while " " in formatted_name:
            formatted_name = formatted_name.replace(" ","_")
        return formatted_name
    
    def remove_focus(self,op):
        current_selected = bpy.context.active_object
        current_selected.select = False
        bpy.data.objects[op['target']].select = True
        return current_selected.name
    
    def return_focus(self,op,previous_selected):
        bpy.data.objects[op['target']].select = False
        bpy.data.objects[previous_selected].select = True
    
    def translate(self,op):
        #obj = bpy.data.objects[op['target']]
        #obj.location.x += op['x']
        #obj.location.y += op['y']
        #obj.location.z += op['z']
        
        previous_selected = self.remove_focus(op)
        
        #get necessary parameters and translate the target object/s
        val = (op['x'],op['y'],op['z'])
        c_axis = (bool(op['caxis_x']),bool(op['caxis_y']),bool(op['caxis_z']))
        bpy.ops.transform.translate(value=val,constraint_axis=c_axis)
        
        self.return_focus(op,previous_selected)
        
    def rotate(self,op):
        #obj = bpy.data.objects[op['target']]
        #value = op['value']
        #obj.rotation_euler.x += (value * op['axis_x'])
        #obj.rotation_euler.y += (value * op['axis_y'])
        #obj.rotation_euler.z += (value * op['axis_z'])
        
        previous_selected = self.remove_focus(op)
        
        val = op['value']
        c_axis = (bool(op['caxis_x']),bool(op['caxis_y']),bool(op['caxis_z']))
        axis = (op['axis_x'],op['axis_y'],op['axis_z'])
        bpy.ops.transform.rotate(value=val,axis=axis,constraint_axis=c_axis)
        
        self.return_focus(op, previous_selected)
    
    def resize(self,op):
        obj = bpy.data.objects[op['target']]
        if op['caxis_x'] == True:
            obj.scale.x *= op['x']
        if op['caxis_y'] == True:
            obj.scale.y *= op['y']
        if op['caxis_z'] == True:
            obj.scale.z *= op['z']
        if not self.check_constraint_axes(op):
            obj.scale.x *= op['x']
            obj.scale.y *= op['y']
            obj.scale.z *= op['z']
        
    def add_cube(self,op):
        loc = (op['loc_x'],op['loc_y'],op['loc_z'])
        bpy.ops.mesh.primitive_cube_add(location=loc)
        
    def check_constraint_axes(self,op):
        '''checks if an operation used a constraint axis'''
        if op['caxis_x'] == False and op['caxis_y'] == False and op['caxis_z'] == False:
            return False
        
        else:
            return True
        