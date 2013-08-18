'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("The Lord of the Rings Online", ".bin")
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
        self.vertBuffs = []
        self.idxBuffs = []
        
    def build_mesh(self, numMesh):
        
        #just load one for now...
        for i in range(1):
            vertBuff, numVerts, vertType = self.vertBuffs[i]
            idxBuff, numIdx = self.idxBuffs[i]
            
            if vertType == 0:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 56, 0)
                rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 56, 24)
            elif vertType == 1:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 61, 0)
                rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 61, 24)
            elif vertType == 2:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 66, 0)
                rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 66, 24)
            elif vertType == 3:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 71, 0)
                rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 71, 24)
            elif vertType == 4:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 76, 0)
                rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 76, 24)
                    
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
        
    def parse_vertices(self, numVerts, vertType):
        
        if vertType == 0:
            vertBuff = self.inFile.readBytes(numVerts*56)
        elif vertType == 1:
            vertBuff = self.inFile.readBytes(numVerts*61)
        elif vertType == 2:
            vertBuff = self.inFile.readBytes(numVerts*66)
        elif vertType == 3:
            vertBuff = self.inFile.readBytes(numVerts*71)
        elif vertType == 4:
            vertBuff = self.inFile.readBytes(numVerts*76)
        else:
            print("unknown vertType: %d" %vertType, self.inFile.tell())
        self.vertBuffs.append([vertBuff, numVerts, vertType])            
        
    def parse_faces(self, numIdx):
        
        idxBuff = self.inFile.readBytes(numIdx*2)
        self.idxBuffs.append([idxBuff, numIdx])
        
    def parse_file(self):
        '''Main parser method'''
        
        self.inFile.read('2L')
        count = self.inFile.readUInt()
        self.inFile.readBytes(count*4)
        numVertGroups = self.inFile.readUInt()
        for i in range(numVertGroups):
            unk1, unk2, vertType, unk3 = self.inFile.read('4b')
            numVerts = self.inFile.readUInt()
            self.parse_vertices(numVerts, vertType)
            self.inFile.read('6f')
            count = self.inFile.readUInt()
            self.inFile.seek(count*4, 1)
        
        numFaceGroups = self.inFile.readUInt()
        for i in range(numFaceGroups):
            numIdx = self.inFile.readUInt()
            self.parse_faces(numIdx)
        self.build_mesh(numVertGroups)