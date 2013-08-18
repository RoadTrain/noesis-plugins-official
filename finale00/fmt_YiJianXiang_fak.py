'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi
import os

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Yi Jian Xiang", ".fak")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 4:
        return 0
    try:
        bs = NoeBitStream(data)
        if noeStrFromBytes(bs.readBytes(4)) != "AKK":
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
    
    #build meshes
    for pose in parser.vertGroups.keys():
        print(pose, len(parser.vertGroups[pose]))
    vertBuffs = parser.vertGroups["walk"]
    for i in range(len(vertBuffs)):
        idxBuff, numIdx, matNum = parser.idxBuffs[i%len(parser.idxBuffs)]
        vertBuff = vertBuffs[i]
        rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 0)
        rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 12)
        rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 24)
        
        matName = parser.matList[matNum].name
        rapi.rpgSetMaterial(matName)
        rapi.rpgSetOption(noesis.RPGOPT_TRIWINDBACKWARD, 1)
        rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)    
    
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
        self.idxBuffs = []
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.vertGroups = {}
        
    def read_name(self, n=4):
        
        return noeStrFromBytes(self.inFile.readBytes(n))
        
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx*2)
    
    def parse_vertices(self, numVerts):

        return self.inFile.readBytes(32*numVerts)
        
    def parse_unk(self, count):
        
        self.inFile.readBytes(count*36)
        
    def parse_materials(self, numMat):
        
        for i in range(numMat):
            matNum = self.inFile.readUInt()
            self.inFile.read('16f')
            self.inFile.readFloat()
            self.inFile.read('3b')
            texPath = self.read_name(1057)
            
            texName = os.path.basename(texPath)
            matName = "material[%d]" %matNum
            material = NoeMaterial(matName, texName)
            self.matList.append(material)
        
    def parse_file(self):
        
        idstring = self.inFile.read('4s')
        null, numVerts, numFaceGroups, faceOfs, numMat, matOfs, numVertGroups, \
            vertOfs = self.inFile.read('8L')
        self.inFile.read('6f')
        self.inFile.seek(256, 1)
        
        for i in range(numFaceGroups):
            unk, matNum, unk, numVerts = self.inFile.read('4H')
            self.inFile.read('6f')
            numIdx = self.inFile.readUInt() * 3
            idxBuff = self.parse_faces(numIdx)
            self.inFile.seek(20, 1)
            
            self.idxBuffs.append([idxBuff, numIdx, matNum])
        
        for i in range(numVertGroups):
            meshName = self.read_name()               
            self.inFile.readFloat()
            numVerts = self.inFile.readUInt()
            vertBuff = self.parse_vertices(numVerts)
            count = self.inFile.readUInt()
            self.parse_unk(count)
            
            if not meshName in self.vertGroups:
                self.vertGroups[meshName] = []            
            self.vertGroups[meshName].append(vertBuff)
            
        self.parse_materials(numMat)