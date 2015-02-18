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
    
    def translate(self,op):
        obj = bpy.data.objects[op['target']]
        obj.location.x += op['x']
        obj.location.y += op['y']
        obj.location.z += op['z']
        
    def rotate(self,op):
        pass
    
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
        
        
    def check_constraint_axes(self,op):
        '''checks if an operation used a constraint axis'''
        if op['caxis_x'] == False and op['caxis_y'] == False and op['caxis_z'] == False:
            return False
        
        else:
            return True
        