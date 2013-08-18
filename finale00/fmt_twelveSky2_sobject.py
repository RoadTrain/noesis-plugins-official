'''rapi model template'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Twelve Sky 2 - static model", ".sobject")
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
    
        self.numVerts = 0
        self.vertBuff = bytes()
    
class ModelParser(object):

    def __init__(self, data):
    
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        
    def parse_vertices(self, numVerts):
    
        return self.inFile.readBytes(numVerts * 32)
        
    def parse_animations(self, numAnims):
    
        self.inFile.readBytes(64 * numAnims)
        
    def parse_bones(self, numBones):
    
        self.inFile.readBytes(32 * numBones)
        
    def parse_faces(self, numIdx):
    
        return self.inFile.readBytes(numIdx * 2)
        
    def parse_file(self):
    
        mesh = Mesh()
        self.inFile.readBytes(120)
        mesh.numVerts, unk1, unk2 = self.inFile.read('3L')
        mesh.numIdx = self.inFile.readUInt() * 3
        self.inFile.readBytes(40)
        mesh.vertBuff = self.parse_vertices(mesh.numVerts)
        self.inFile.readBytes(unk1 * 32)
        mesh.idxBuff = self.parse_faces(mesh.numIdx)
        return mesh

class SanaeParser(object):
    
    def __init__(self, data):    
        '''Initialize some data'''
        
        self.inFile = NoeBitStream(data)
        self.meshList = []
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
      
    def build_mesh(self):
    
        for i in range(len(self.meshList)):
            mesh = self.meshList[i]
            rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 32, 0)
            rapi.rpgBindNormalBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 32, 12)
            rapi.rpgBindUV1BufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 32, 24)
            
            meshName = "Mesh%d" %i
            rapi.rpgSetName(meshName)
            mat = self.matList[i]
            rapi.rpgSetMaterial(mat.name)
            rapi.rpgCommitTriangles(mesh.idxBuff, noesis.RPGEODATA_USHORT, mesh.numIdx, noesis.RPGEO_TRIANGLE, 1)
        
    def decompData(self, size, compSize):
    
        compData = self.inFile.readBytes(compSize)
        return rapi.decompInflate(compData, size)
        
    def parse_model(self, data):
    
        parser = ModelParser(data)
        mesh = parser.parse_file()
        self.meshList.append(mesh)
        
    def parse_texture(self, data):
    
        matNum = len(self.matList)
        mat = NoeMaterial("material%d" %matNum, "")
        texture = rapi.loadTexByHandler(data, ".dds")
        if texture:
            texture.name = "texture%d" %(len(self.texList))
            self.texList.append(texture)
            mat.setTexture(texture.name)
        self.matList.append(mat)
            
        
    def parse_file(self):
        '''Main parser method'''
        
        numFiles = self.inFile.readUInt()
        for i in range(numFiles):
            unk, size, compSize = self.inFile.read('3L')
            data = self.decompData(size, compSize)
            self.parse_model(data)
            
            unk, size, compSize = self.inFile.read('3L')
            data = self.decompData(size, compSize)
            self.parse_texture(data)
            self.inFile.read('2L')
        self.build_mesh()