'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Asda 2", ".jbm")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    return 1

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

class Mesh(object):
    '''A mesh object. For convenience'''
    
    def __init__(self):
        
        numVerts = 0
        numIdx = 0
        vertBuff = bytes()
        idxBuff = bytes()

class SanaeParser(object):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.meshList = []
        
    def build_meshes(self):
        
        for mesh in self.meshList:
            
            rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 44, 0)
            rapi.rpgBindNormalBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 44, 12)
            rapi.rpgBindUV1BufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 44, 28)
            rapi.rpgCommitTriangles(mesh.idxBuff, noesis.RPGEODATA_USHORT, mesh.numIdx, noesis.RPGEO_TRIANGLE, 1)
    
    def read_name(self, n):
        
        return noeStrFromBytes(self.inFile.readBytes(n))
    
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx*2)
    
    def parse_vertices(self, numVerts):
        
        return self.inFile.readBytes(numVerts*44)
    
    def parse_unk(self, numVerts):
        
        return self.inFile.readBytes(numVerts*12)
    
    def parse_mesh_header(self, numMesh):
        
        for i in range(numMesh):
            mesh = Mesh()
            self.inFile.readUInt()
            self.inFile.seek(36, 1)
            numVerts = self.inFile.readUInt()
            numIdx = self.inFile.readUInt() * 3
            self.inFile.seek(456, 1)
            self.inFile.readUInt()
            #meshName = self.read_name(32)
            self.inFile.seek(32, 1)
            self.inFile.seek(128, 1)
            
            mesh.numVerts = numVerts
            mesh.numIdx = numIdx
            self.meshList.append(mesh)
            
    def parse_mesh_data(self, numMesh):
        
        for mesh in self.meshList:
            mesh.idxBuff = self.parse_faces(mesh.numIdx)
            mesh.vertBuff = self.parse_vertices(mesh.numVerts)
            self.parse_unk(mesh.numVerts)
        
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.inFile.readUInt()
        self.inFile.readUInt()
        numMesh = self.inFile.readUInt()
        self.inFile.seek(40, 1)
        numMat = self.inFile.readUInt()
        self.inFile.seek(324, 1)
        #modelName = self.read_name(56)
        self.inFile.seek(56, 1)
        self.inFile.read('16f')
        self.inFile.read('3f')
        self.inFile.readInt()
        self.inFile.read('3L')
        for i in range(numMat):
            #self.read_name(32)
            self.inFile.seek(32, 1)
        
        self.parse_mesh_header(numMesh)
        self.parse_mesh_data(numMesh)
        #self.parse_bones(numBones)
        print(self.inFile.tell())
        self.build_meshes()