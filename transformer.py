import bpy

class Transformer:
    
    def add(self,op):
        '''transformation function for conflicting object names
        
        Parameters
        op           -- a dictionary object representing the operation in consideration
        
        Return Value
        
        revised_op   -- an operation (dict) with revised parameters
        
        '''
        
        obj_name = op['active_object']
        
        if obj_name in bpy.data.objects:
            #modify the name of the object
            
            obj_type = obj_name.split(".")[0]
            new_name = obj_type
            num_id = 1
            while new_name in bpy.data.objects:
                new_name = obj_type + "." + str(num_id).zfill(3)
                num_id += 1

            op['active_object'] = new_name
            
        return op
            
            