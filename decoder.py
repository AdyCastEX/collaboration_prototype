import bpy

class Decoder:
    
    def format_op_name(self,op_name):
        '''converts an operator name to a format that follows method naming conventions
        
        Parameters:
        op_name -- the name of the operator from the info space
        
        Return Value
        formatted_name -- the properly formatted name of the operator
        
        '''
        #convert the op name to lowercase
        formatted_name = op_name.lower()
        #replace all spaces with underscores
        while " " in formatted_name:
            formatted_name = formatted_name.replace(" ","_")
        return formatted_name
    
    def remove_focus(self,op):
        '''moves the selection from the currently selected object to target object/s 
        
        Parameters
        op -- a dict object containing the information of an operation
        
        Return Type
        selected_names    -- a list containing the names of the objects that were selected before shifting focus
        '''
        selected_names = []
        current_selected = bpy.context.selected_objects
        for obj in current_selected:
            obj.select = False
            selected_names.append(obj.name)
            
        for target in op['targets']:
            try:
                bpy.data.objects[target].select = True
            except KeyError:
                pass
        
        return selected_names
    
    def return_focus(self,op,previous_selected):
        '''moves the selection back to the previously selected object/s 
        Parameters
        
        op -- a dict object containing info of an operation
        previous_selected -- a string containing the name/s of the previously selected object/s
        
        '''
        
        try:
            #handle Key errors in cases like delete where previous objects are removed
            for target in op['targets']:
                bpy.data.objects[target].select = False
        except KeyError:
            pass
        
        try:        
            for obj in previous_selected:
                bpy.data.objects[obj].select = True
        except KeyError:
            pass
        
    
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
        #obj = bpy.data.objects[op['target']]
        #if op['caxis_x'] == True:
        #    obj.scale.x *= op['x']
        #if op['caxis_y'] == True:
        #    obj.scale.y *= op['y']
        #if op['caxis_z'] == True:
        #    obj.scale.z *= op['z']
        #if not self.check_constraint_axes(op):
        #    obj.scale.x *= op['x']
        #    obj.scale.y *= op['y']
        #    obj.scale.z *= op['z']
        previous_selected = self.remove_focus(op)
        
        val = (op['x'],op['y'],op['z'])
        c_axis = (bool(op['caxis_x']),bool(op['caxis_y']),bool(op['caxis_z']))
        bpy.ops.transform.resize(value=val,constraint_axis=c_axis)
        
        self.return_focus(op, previous_selected)
        
    def add_cube(self,op):
        
        previous_selected = self.remove_focus(op)
        
        loc = (op['loc_x'],op['loc_y'],op['loc_z'])
        bpy.ops.mesh.primitive_cube_add(location=loc)
        
        self.return_focus(op, previous_selected)
        
    def delete(self,op):
        previous_selected = self.remove_focus(op)
        
        bpy.ops.object.delete(use_global=op['use_global'])
        
        self.return_focus(op, previous_selected)
        
    def check_constraint_axes(self,op):
        '''checks if an operation used a constraint axis'''
        if op['caxis_x'] == False and op['caxis_y'] == False and op['caxis_z'] == False:
            return False
        
        else:
            return True
        