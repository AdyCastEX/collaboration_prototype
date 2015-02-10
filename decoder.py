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
        