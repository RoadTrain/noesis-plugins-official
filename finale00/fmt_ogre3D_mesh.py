'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Dragon Oath", ".mesh")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 24:
        return 0
    try:
        bs = NoeBitStream(data)
        chunk = bs.readUShort()
        idstring = noeStrFromBytes(bs.readBytes(15))
        if idstring != "[MeshSerializer":
            return 0
        return 1
    except:
        return 0

def noepyLoadModel(data, mdlList):
    '''Build the model, set materials, bones, and animations. You do not
    need all of them as long as they are empty lists (they are by default)'''
    
    ctx = rapi.rpgCreateContext()
    parser = SanaeParser(data)
    parser.parse_file()
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
    mdl.setBones(parser.boneList)
    mdl.setAnims(parser.animList)
    mdlList.append(mdl)
    return 1

class SanaeParser(object):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.vertBuffs = []
        self.idxBuffs = []
        self.numVerts = 0
        self.vertSize = 0
        
    def plot_points(self, numVerts):
    
        rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, numVerts, noesis.RPGEO_POINTS, 1)
        
    def build_meshes(self):
        
        for i in range(len(self.vertBuffs)):
            print(len(self.idxBuffs), len(self.vertBuffs))
            vertBuff, numVerts, vertSize = self.vertBuffs[i]
            idxBuff, numIdx = self.idxBuffs[i]

            if vertSize == 24:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 24, 0)
            elif vertSize == 32:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 0)
            self.plot_points(numVerts)
            #rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
        
    def read_name(self):
        
        string = []
        char = self.inFile.readByte()
        while char != 0x0A:
            string.append(char)
            char = self.inFile.readByte()
        
    def parse_mesh(self):
        
        self.inFile.readByte()
        
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx * 2)
        
    def parse_submesh(self):
        
        self.read_name()
        self.inFile.readByte()
        numIdx = self.inFile.readUInt()
        self.inFile.readByte()
        idxBuff = self.parse_faces(numIdx)
        self.idxBuffs.append([idxBuff, numIdx])
        
    def parse_geometry(self):
        
        self.numVerts = self.inFile.readUInt()
        
    def parse_vertex_buffer_data(self):
       
        vertBuff = self.inFile.readBytes(self.numVerts * self.vertSize)
        self.vertBuffs.append([vertBuff, self.numVerts, self.vertSize])
        
    def parse_vertex_buffer(self):
        
        self.inFile.readUShort()
        self.vertSize = self.inFile.readUShort()
        
    def parse_file(self):
        '''Main parser method'''
        
        #header
        chunk = self.inFile.readUShort()
        self.read_name()
        
        #data chunks
        while self.inFile.tell() != self.inFile.dataSize:
            chunk = self.inFile.readUShort()
            
            #chunk size includes these two values
            size = self.inFile.readUInt() - 6
            if chunk == 0x3000:
                self.parse_mesh()
            elif chunk == 0x4000:
                self.parse_submesh()
            #elif chunk == 0x4010:
                #self.parse_submesh_operation()
            #elif chunk == 0x4100:
                #self.parse_submesh_bone_assignment()
            #elif chunk == 0x4200:
                #self.parse_submesh_texture_alias()
            elif chunk == 0x5000:
                self.parse_geometry()
            #elif chunk == 0x5100:
                #self.parse_geometry_vertex_declaration()
            #elif chunk == 0x5110:
                #self.parse_geometry_element()
            elif chunk == 0x5200:
                self.parse_vertex_buffer()
            elif chunk == 0x5210:
                self.parse_vertex_buffer_data()
                break
            #elif chunk == 0x6000:
                #self.parse_mesh_skeleton_link()
            #elif chunk == 0x7000:
                #self.parse_mesh_bone_assignment()
            #elif chunk == 0x8000:
                #self.parse_mesh_lod()
            #elif chunk == 0x8100:
                #self.parse_mesh_lod_usage()
            #elif chunk == 0x8110:
                #self.parse_mesh_lod_manual()
            #elif chunk == 0x8120:
                #self.parse_mesh_load_generated()
            #elif chunk == 0x9000:
                #self.parse_mesh_bounds()
            #elif chunk == 0xA000:
                #self.parse_submesh_name_table()
            #elif chunk == 0xA100:
                #self.parse_submesh_name_table_element()
            #elif chunk == 0xB000:
                #self.parse_edge_lists()
            #elif chunk == 0xB100:
                #self.parse_edge_list_lod()
            #elif chunk == 0xB110:
                #self.parse_edge_group()
            #elif chunk == 0xC000:
                #self.parse_poses()
            #elif chunk == 0xC100:
                #self.parse_pose()
            #elif chunk == 0xC111:
                #self.parse_pose_vertex()
            #elif chunk == 0xD000:
                #self.parse_animations()
            #elif chunk == 0xD100:
                #self.parse_animation()
            #elif chunk == 0xD110:
                #self.parse_animation_track()
            #elif chunk == 0xD111:
                #self.parse_aimation_morph_keyframe()
            #elif chunk == 0xD112:
                #self.parse_animation_pose_keyframe()
            #elif chunk == 0xD113:
                #self.parse_animation_pose_ref()
            #elif chunk == 0xE000:
                #self.parse_teable_extremes()
            else:
                self.inFile.seek(size, 1)
        print(self.inFile.tell())
        self.build_meshes()

             #Ogre::M_TABLE_EXTREMES = 0xE000, Ogre::M_GEOMETRY_NORMALS = 0x5100, Ogre::M_GEOMETRY_COLOURS = 0x5200, Ogre::M_GEOMETRY_TEXCOORDS = 0x5300             