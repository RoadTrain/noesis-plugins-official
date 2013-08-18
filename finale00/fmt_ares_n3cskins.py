'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Ares", ".n3cskins")
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

class SanaeParser(object):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []        
                
    def read_name(self):
        
        return noeStrFromBytes(self.inFile.readBytes(self.inFile.readUInt()))
    
    def parse_vertices(self, numVerts):
        
        return self.inFile.readBytes(24*numVerts)
        
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx*2)
    
    def parse_uv(self, numUV):
        
        return self.inFile.readBytes(numUV*8)
        
    def parse_uv_index(self, numIdx):
        
        self.uvIndices = self.inFile.readBytes(numIdx*2)
        
    def parse_file(self):
        
        meshName = self.read_name()
        matName = self.read_name()
        texName = meshName
        
        numIdx = self.inFile.readUInt() * 3
        numVerts, numUV = self.inFile.read('2L')
        vertBuff = self.parse_vertices(numVerts)
        idxBuff = self.parse_faces(numIdx)
        uvBuff = self.parse_uv(numUV)
        self.parse_uv_index(numIdx)
        
        #create material
        material = NoeMaterial(matName, texName)
        self.matList.append(material)        
        
        #build mesh
        rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 24, 0)
        rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 24, 12)
        
        #commit triangles
        rapi.rpgSetMaterial(texName)
        rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
        
        #what to do with these UV's?
        rapi.rpgBindUV1Buffer(uvBuff, noesis.RPGEODATA_FLOAT, 8)        
        
        