'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Ultimate Mortal Kombat", ".meshset")
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
       
    def plot_points(self, numVerts):
           
        rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, numVerts, noesis.RPGEO_POINTS, 1)       
        
    def read_name(self):
        
        return noeStrFromBytes(self.inFile.readBytes(64))
    
    def parse_faces(self, numIdx):
    
        return self.inFile.readBytes(numIdx*2)
    
    def parse_vertices(self, numVerts):
        
        vertBuff = self.inFile.readBytes(numVerts*26)
        rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 26, 6)
        #rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 12)
        #rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 24)   
        
        #show the vertices        
        self.plot_points(numVerts)
        
    def parse_file(self):
        
        numMesh = self.inFile.readUInt()
        #for i in range(numMesh):
        for i in range(2):
            meshName = self.read_name()
            matName = self.read_name()
            numVerts = self.inFile.readUInt()
            numIdx = self.inFile.readUInt() * 3
            self.inFile.readFloat()
            idxBuff = self.parse_faces(numIdx)
            self.parse_vertices(numVerts)
        
        #draw the triangles
        rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)