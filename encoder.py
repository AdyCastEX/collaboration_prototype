import bpy
import json

class Encoder:
    
    def create_generic_operation(self,op_name,target_objects,active_object,mode):
        ''' creates a generic encoded operation 
        
        Parameters:
        op_name -- name of the operator
        target_objects -- a list of objects that are involved in the operation
        mode -- the mode (e.g. object, edit) when the operator was called
        
        '''
        op = {}
        op['name'] = op_name
        op['targets'] = target_objects
        op['active_object'] = active_object
        op['mode'] = mode
        return op
    
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
    
    def get_obj_names(self,target_objects):
        '''gets the names of multiple objects
        
        Parameters
        target_objects    -- a list containing target objects
        
        Return Value
        obj_names         -- a list of names of target objects in string format
        
        '''
        obj_names = []
        for obj in target_objects:
            obj_names.append(obj.name)
            
        return obj_names
        
    
    def translate(self,operator,target_objects,active_object,mode):
        '''creates an operation with attributes specific to a translation'''
        op = self.create_generic_operation(operator.name,target_objects,active_object,mode)
        op['x'],op['y'],op['z'] = operator.properties['value']
        op['caxis_x'],op['caxis_y'],op['caxis_z'] = operator.properties['constraint_axis']
        return op
    
    def rotate(self,operator,target_objects,active_object,mode):
        '''creates an operation with attributes specific to a rotation'''
        op = self.create_generic_operation(operator.name,target_objects,active_object,mode)
        op['value'] = operator.properties['value']
        op['caxis_x'],op['caxis_y'],op['caxis_z'] = operator.properties['constraint_axis']
        op['axis_x'],op['axis_y'],op['axis_z'] = operator.properties['axis']
        return op
    
    def resize(self,operator,target_objects,active_object,mode):
        '''creates an operation with attributes specific to a resize/scale'''
        op = self.create_generic_operation(operator.name, target_objects,active_object, mode)
        op['x'],op['y'],op['z'] = operator.properties['value']
        op['caxis_x'],op['caxis_y'],op['caxis_z'] = operator.properties['constraint_axis']
        return op
        
    def delete(self,operator,target_objects,active_object,mode):
        '''creates an operation with attributes specific to a delete'''
        if target_objects == []:
            selected_objects = json.loads(bpy.context.scene.active_obj_name)
            op = self.create_generic_operation(operator.name, selected_objects,active_object, mode)
        else:
            op = self.create_generic_operation(operator.name, target_objects,active_object, mode)
        op['use_global'] = operator.properties['use_global']
        return op
    
    def add_generic_object(self,operator,target_objects,active_object,mode):
        '''creates an operation with attributes of any type of object'''
        op = self.create_generic_operation(operator.name, target_objects,active_object, mode)
        op['loc_x'],op['loc_y'],op['loc_z'] = operator.properties['location']
        return op
    
    def add_cube(self,operator,target_objects,active_object,mode):
        '''creates an operation with attributes specific to adding a primitive cube'''
        op = self.add_generic_object(operator,target_objects,active_object,mode)        
        return op
    
    def add_circle(self,operator,target_objects,active_object,mode):
        '''creates an operation with attributes specific to adding a primitive circle'''
        op = self.add_generic_object(operator, target_objects,active_object, mode)        
        return op
    
    def add_plane(self,operator,target_objects,active_object,mode):
        '''creates an operation with attributes specific to adding a primitive plane'''
        op = self.add_generic_object(operator, target_objects,active_object, mode)        
        return op
    
    def add_uv_sphere(self,operator,target_objects,active_object,mode):
        '''creates an operation with attributes specific to adding a primitive UV sphere'''
        op = self.add_generic_object(operator, target_objects,active_object, mode)        
        return op
    
    def add_ico_sphere(self,operator,target_objects,active_object,mode):
        '''creates an operation with attributes specific to a adding a primitive ico sphere'''
        op = self.add_generic_object(operator, target_objects,active_object, mode)        
        return op
    
    def add_cylinder(self,operator,target_objects,active_object,mode):
        '''creates an operation with attributes specific to adding a primitive cylinder'''
        op = self.add_generic_object(operator, target_objects,active_object, mode)        
        return op
    
    def add_cone(self,operator,target_objects,active_object,mode):
        '''creates an operation with attributes specific to adding a primitive cone'''
        op = self.add_generic_object(operator, target_objects,active_object, mode)        
        return op
        
    def add_grid(self,operator,target_objects,active_object,mode):
        '''creates an operation with attributes specific to adding a primitive grid'''
        op = self.add_generic_object(operator, target_objects,active_object, mode)        
        return op
    
    def add_monkey(self,operator,target_objects,active_object,mode):
        '''creates an operation with attributes specific to adding a primitive monkey object'''
        op = self.add_generic_object(operator, target_objects,active_object, mode)        
        return op
    
    def add_torus(self,operator,target_objects,active_object,mode):
        '''creates an operation with attributes specific to adding a primitive torus object '''
        op = self.add_generic_object(operator, target_objects, active_object, mode)
        return op    