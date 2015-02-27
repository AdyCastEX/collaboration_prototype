import bpy
import bmesh

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
    
    def focus_object(self,op):
        ''' moves the selection to a collection of objects
        
        Parameters
        op    --a dict object representing an operation
        
        '''
        for target in op['targets']:
            try:
                bpy.data.objects[target].select = True
            except KeyError:
                pass
            
    def refocus_object_mode(self,target_objects,flag):
        '''moves the selection to a collection of objects
        
        Parameters
        target_objects      -- a list of names of target objects
        flag                -- a boolean value that indicates the operation
                            -- True -> select objects
                            -- False -> deselect objects
                            
        Return Value
        deselected_objects  -- a list of object names that were deselected (empty if flag == True)
        '''
        
        deselected_objects = []
        
        for target in target_objects:
            try:
                bpy.data.objects[target].select = flag
                if flag == False:
                    deselected_objects.append(target)
            except KeyError:
                pass
            
        return deselected_objects
    
    def refocus_edit_mode(self,active_object,internals,flag):
        
        deselected_internals = {}
        deselected_verts = []
        deselected_edges = []
        deselected_faces = []
        
        bm = bmesh.from_edit_mesh(bpy.data.objects[active_object].data)
        for i in internals['verts']:
            bm.verts[i].select = flag
            if flag == False:
                deselected_verts.append(i)
        for i in internals['edges']:
            bm.edges[i].select = flag
            if flag == False:
                deselected_edges.append(i)
        for i in internals['faces']:
            bm.faces[i].select = flag
            if flag == False:
                deselected_faces.append(i)
                
        deselected_internals['verts'] = deselected_verts
        deselected_internals['edges'] = deselected_edges
        deselected_internals['faces'] = deselected_faces
        
        if flag == False:
            return deselected_internals
        elif flag == True:
            return {}
            
    def focus_edit(self,op):
        '''moves the selection to a collection of vertices,edges and faces
        
        Parameters
        op     --a dict object representing an operation
        
        ''' 
        bm = bmesh.from_edit_mesh(bpy.data.objects[op['active_object']].data)
        for i in op['verts']:
            bm.verts[i].select = True
            
        for i in op['edges']:
            bm.edges[i].select = True
            
        for i in op['faces']:
            bm.faces[i].select = True
        
        
    
    def remove_focus(self,op):
        '''moves the selection from the currently selected object to target object/s 
        
        Parameters
        op -- a dict object containing the information of an operation
        
        Return Type
        focus             -- a dict containing the following:
           selected       -- a list containing the names of the objects that were selected before shifting focus
           active         -- a string containing the name of the active object
           mode           -- a string containing the current mode ('EDIT_MESH','OBJECT')
        '''
        #current_selected = []
        #for obj in bpy.context.selected_objects:
        #    obj.select = False
        #    current_selected.append(obj.name)
        current_active = bpy.context.active_object.name
        current_mode = bpy.context.mode
        current_selected = ''
        current_internals = ''
        
        if current_mode in ('OBJECT'):
            selected_objs = self.get_obj_names(bpy.context.selected_objects)
            current_selected = self.refocus_object_mode(selected_objs,False)
            
        elif current_mode in ('EDIT_MESH'):
            selected_internals = self.get_internals(current_active)
            current_internals = self.refocus_edit_mode(current_active,selected_internals,False)
        
        if op['mode'] != current_mode:
            print("From: {0}".format(bpy.context.mode))
            bpy.ops.object.editmode_toggle()
            print("To: {0}".format(bpy.context.mode))
            
            new_mode = bpy.context.mode
            
            if new_mode in ('OBJECT'):
                selected_objs = self.get_obj_names(bpy.context.selected_objects)
                current_selected = self.refocus_object_mode(selected_objs,False)
                
            elif new_mode in ('EDIT_MESH'):
                selected_internals = self.get_internals(current_active)
                current_internals = self.refocus_edit_mode(current_active,selected_internals,False)
            
        
        if op['mode'] in ('OBJECT'):
            self.refocus_object_mode(op['targets'], True)
                 
        elif op['mode'] in ('EDIT_MESH'):
            internals = {'verts': op['verts'], 'edges' : op['edges'], 'faces' : op['faces']}
            self.refocus_edit_mode(op['active_object'], internals,True)
            
        try:
            bpy.context.scene.objects.active = bpy.data.objects[op['active_object']]
        except KeyError:
            pass
            
        focus = {
            'selected' : current_selected,
            'active' : current_active,
            'mode' : current_mode,
            'internals' : current_internals
        }
        
        return focus
    
    def return_focus(self,op,focus):
        '''moves the selection back to the previously selected object/s 
        Parameters
        
        op -- a dict object containing info of an operation
        previous_selected -- a string containing the name/s of the previously selected object/s
        
        '''
        current_mode = bpy.context.mode
        
        try:
            #handle Key errors in cases like delete where previous objects are removed
            if op['mode'] in ('OBJECT'):
                self.refocus_object_mode(op['targets'], False)
            elif op['mode'] in ('EDIT_MESH'):
                internals = {'verts' : op['verts'],'edges' : op['edges'],'faces' : op['faces']}
                self.refocus_edit_mode(op['active_object'], internals,False)
        except KeyError:
            pass
        
        if current_mode != focus['mode']:
            
            if current_mode in ('OBJECT'):
                self.refocus_object_mode(focus['selected'],True)
            
            elif current_mode in ('EDIT_MESH'):
                self.refocus_edit_mode(focus['active'], focus['internals'], True)
            
            print("From: {0}".format(bpy.context.mode))
            bpy.ops.object.editmode_toggle()
            print("To: {0}".format(bpy.context.mode))
        
        try:        
            if focus['mode'] in ('OBJECT'):
                self.refocus_object_mode(focus['selected'], True)
            elif focus['mode'] in ('EDIT_MESH'):
                self.refocus_edit_mode(focus['active'], focus['internals'],True)
        except KeyError:
            pass
        
        try:
            bpy.context.scene.objects.active = bpy.data.objects[focus['active']]
        except KeyError:
            pass
        
        
    def get_internals(self,active_object):
        bm = bmesh.from_edit_mesh(bpy.data.objects[active_object].data)
        
        verts = [i.index for i in bm.verts if i.select]
        edges = [i.index for i in bm.edges if i.select]
        faces = [i.index for i in bm.faces if i.select]
        
        internals = {
            'verts' : verts,
            'edges' : edges,
            'faces' : faces
        }
        
        return internals
        
    
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
        
    def add_circle(self,op):
        
        previous_selected = self.remove_focus(op)
        
        loc = (op['loc_x'],op['loc_y'],op['loc_z'])
        bpy.ops.mesh.primitive_circle_add(location=loc)
        
        self.return_focus(op, previous_selected)
    
    def add_plane(self,op):
        previous_selected = self.remove_focus(op)
        
        loc = (op['loc_x'],op['loc_y'],op['loc_z'])
        bpy.ops.mesh.primitive_plane_add(location=loc)
        
        self.return_focus(op, previous_selected)
    
    def add_uv_sphere(self,op):
        previous_selected = self.remove_focus(op)
        
        loc = (op['loc_x'],op['loc_y'],op['loc_z'])
        bpy.ops.mesh.primitive_uv_sphere_add(location=loc)
        
        self.return_focus(op, previous_selected)
    
    def add_ico_sphere(self,op):
        previous_selected = self.remove_focus(op)
        
        loc = (op['loc_x'],op['loc_y'],op['loc_z'])
        bpy.ops.mesh.primitive_ico_sphere_add(location=loc)
        
        self.return_focus(op, previous_selected)
    
    def add_cylinder(self,op):
        previous_selected = self.remove_focus(op)
        
        loc = (op['loc_x'],op['loc_y'],op['loc_z'])
        bpy.ops.mesh.primitive_cylinder_add(location=loc)
        
        self.return_focus(op, previous_selected)
    
    def add_cone(self,op):
        previous_selected = self.remove_focus(op)
        
        loc = (op['loc_x'],op['loc_y'],op['loc_z'])
        bpy.ops.mesh.primitive_cone_add(location=loc)
        
        self.return_focus(op, previous_selected)
    
    def add_grid(self,op):
        previous_selected = self.remove_focus(op)
        
        loc = (op['loc_x'],op['loc_y'],op['loc_z'])
        bpy.ops.mesh.primitive_grid_add(location=loc)
        
        self.return_focus(op, previous_selected)

    def add_monkey(self,op):
        previous_selected = self.remove_focus(op)
        
        loc = (op['loc_x'],op['loc_y'],op['loc_z'])
        bpy.ops.mesh.primitive_monkey_add(location=loc)
        
        self.return_focus(op, previous_selected)
        
    def add_torus(self,op):
        previous_selected = self.remove_focus(op)
        
        loc = (op['loc_x'],op['loc_y'],op['loc_z'])
        bpy.ops.mesh.primitive_torus_add(location=loc)
        
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
        