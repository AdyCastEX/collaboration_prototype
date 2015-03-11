import bpy
import json

class Encoder:
    
    def create_generic_operation(self,op_name,target_objects,active_object,mode):
        ''' creates a generic encoded operation 
        
        Parameters:
        op_name        -- name of the operator
        target_objects -- a dictionary object containing the following:
            objects    -- a list of object names
            verts      -- a list of indices of selected vertices
            edges      -- a list of indices of selected edges
            faces      -- a list of indices of selected faces
        active_object  -- a string containing the name of the active object
        mode           -- the mode (e.g. 'OBJECT', 'EDIT_MESH') when the operator was called
        
        Return Value
        op             -- a dictionary representing an operation
        
        '''
        op = {}
        op['name'] = op_name
        op['targets'] = target_objects['objects']
        op['active_object'] = active_object
        op['mode'] = mode
        
        if mode in ('EDIT_MESH'):
            op['verts'] = target_objects['verts']
            op['edges'] = target_objects['edges']
            op['faces'] = target_objects['faces']
        return op
    
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
        
        #since delete removes targets, use the saved properties to get the last selected targets
        if target_objects == {} or (target_objects['verts'] == [] and target_objects['edges'] == [] and target_objects['faces'] == []):
            selected_objects = {}
            selected_objects['objects'] = json.loads(bpy.context.scene.active_obj_name)
            if mode in ('EDIT_MESH'):
                internals = json.loads(bpy.context.scene.selected_internals)
                selected_objects['verts'] = internals['verts']
                selected_objects['edges'] = internals['edges']
                selected_objects['faces'] = internals['faces']
            op = self.create_generic_operation(operator.name, selected_objects,active_object, mode)
        else:
            op = self.create_generic_operation(operator.name, target_objects,active_object, mode)
            
        if mode in ('OBJECT'):
            op['use_global'] = operator.properties['use_global']
        elif mode in ('EDIT_MESH'):
            op['type'] = operator.type
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