'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Unity Engine", ".43")
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
    
    def __init__(self):
        
        self.name = ""
        self.numIdx = 0
        self.numVerts = 0
        self.vertSize = 0
        self.idxBuff = bytes()
        self.vertBuff = bytes()

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
        
        vertStart = 0
        idxStart = 0
        for mesh in self.meshList:
            
            vertEnd = vertStart + mesh.numVerts * self.vertSize
            idxEnd = idxStart + mesh.numIdx * 2
            
            vertBuff = self.vertBuff[vertStart : vertEnd]
            idxBuff = self.idxBuff[idxStart : idxEnd]
            
            vertStart = vertEnd
            idxStart = idxEnd
            
            if self.vertSize == 56:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 56, 0)
                rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 56, 12)
                
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, mesh.numIdx, noesis.RPGEO_TRIANGLE_STRIP, 1)     
        
    def read_name(self):
        
        #string = self.inFile.readBytes(n)
        return noeStrFromBytes(string)
        
    def parse_materials(self, numMat):
            
        pass
        
    def parse_textures(self, numTex):
            
        pass    
        
    def parse_vertices(self, numVerts):
        
        return self.inFile.readBytes(numVerts * vertSize)
    
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx * 2)
    
    def parse_meshes(self, numMesh):
        
        for i in range(numMesh):
            self.inFile.read('7L')
            self.inFile.read('6f')
            
    def parse_mesh_info(self, numMesh):
        
        for i in range(numMesh):
            mesh = Mesh()
            mesh.idxStart = self.inFile.readUInt()
            mesh.numIdx = self.inFile.readUInt()
            mesh.idxSize = self.inFile.readUInt()
            self.inFile.read('2L')
            mesh.numVerts = self.inFile.readUInt()
            self.inFile.read('6f')
            
            self.meshList.append(mesh)
    
    def parse_bones(self, numBones):
        
        pass
    
    def parse_unk1(self):
        
        count = self.inFile.readShort()
        if count == 0:
            count = self.inFile.readUInt()
        else:
            self.inFile.readShort()
        self.inFile.seek(count * 32, 1)
        
    def parse_unk2(self, count):
        
        self.inFile.seek(count * 64, 1)
    
    def parse_file(self):
        '''Main parser method'''
        
        numMesh = self.inFile.readUInt()
        self.parse_mesh_info(numMesh)
            
        # idx buffer
        unk = self.inFile.readUInt()
        size = self.inFile.readUInt()
        self.idxBuff = self.inFile.readBytes(size)
        #self.inFile.readShort() #null
        
        # unk 1
        self.parse_unk1()
        
        # unk 2. Matrices?
        count2 = self.inFile.readUInt()
        self.parse_unk2(count2)
        
        # vert buff
        
        self.inFile.readUInt()
        numVerts = self.inFile.readUInt()
        self.inFile.read('2L')
        self.vertSize = self.inFile.readUInt()
        self.inFile.seek(52, 1)
        size = self.inFile.readUInt()
        print(size)
        self.vertBuff = self.inFile.readBytes(size)
        
        self.build_meshes()