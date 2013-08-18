'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi
from Sanae3D.Sanae import SanaeObject
import os

MODE = 0

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Voyage Century Online", ".gm")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 4:
        return 0
    try:
        bs = NoeBitStream(data)
        idstring = noeStrFromBytes(bs.readBytes(4))
        if idstring != "50.1":
            return 0
        return 1
    except:
        return 0

def load_all_models(mdlList):
    '''Load all models'''

    #carry over from previous models
    matList = []
    texList = []

    dirPath = rapi.getDirForFilePath(rapi.getInputName())
    fileList = [file for file in os.listdir(dirPath) if file.lower().endswith(".gm")]
    for file in fileList:
        f = open(dirPath + file, 'rb')
        data2 = f.read()
        parser = SanaeParser(data2)
        parser.parse_file()
        matList.extend(parser.matList)
        texList.extend(parser.texList)
        mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(texList, matList))
    mdlList.append(mdl)    
    
def load_single_model(data, mdlList):
    '''Loads a single model. For testing purposes'''
    
    parser = SanaeParser(data)
    parser.parse_file()
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
    mdlList.append(mdl)       

def noepyLoadModel(data, mdlList):
    '''Load the model'''
    
    ctx = rapi.rpgCreateContext()
    if MODE == 1:
        load_all_models(mdlList)
    else:
        load_single_model(data, mdlList)
    return 1

class SanaeParser(SanaeObject):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        super(SanaeParser, self).__init__(data)
        self.indexCounts = []
        self.idxBuffs = []
        
    def build_mesh(self, meshType):
        
        for i in range(len(self.idxBuffs)):
            idxBuff, numIdx = self.idxBuffs[i]
            
            if meshType == 0:
                rapi.rpgSetOption(noesis.RPGOPT_TRIWINDBACKWARD, 1)
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
        
    def read_name(self):
        
        return self.inFile.readString()
    
    def parse_face_info(self, numMat):
        
        for i in range(numMat):
            self.inFile.read('3L')
            self.inFile.read('4f')
            self.inFile.readUInt()
            numIdx = self.inFile.readUInt() * 3
            self.inFile.read('5L')
            self.inFile.read('11f')
            self.inFile.readUInt()
            
            self.indexCounts.append(numIdx)
            
    def parse_unk1(self, count):
        
        for i in range(count):
            self.inFile.readUInt()
            self.inFile.read('4l')
            self.inFile.readUInt()
            self.inFile.read('3f')
            self.inFile.read('5L')
            
    def parse_unk2(self, count):
        
        for i in range(count):
            self.inFile.seek(108, 1)
            
    def parse_faces(self):
        
        total = 0
        for numIdx in self.indexCounts:
            idxBuff = self.inFile.readBytes(numIdx*2)
            self.idxBuffs.append([idxBuff, numIdx])
            
            total += numIdx
            
        print(total, "indices")
        
    def parse_vertices(self, numVerts, vertType):
        
        if vertType == 0:
            vertBuff = self.inFile.readBytes(numVerts*36)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 36, 0)
            rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 36, 12)
            rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 36, 28)        
        elif vertType == 1:
            vertBuff = self.inFile.readBytes(numVerts*44)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 44, 0)
            rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 44, 12)
            rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 44, 28)
        elif vertType == 4:
            vertBuff = self.inFile.readBytes(numVerts*44)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 44, 0)
            rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 44, 20)      
            rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 44, 36)
        elif vertType == 5:
            vertBuff = self.inFile.readBytes(numVerts*52)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 52, 0)
            rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 52, 20)      
            rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 52, 36)            
            
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.read_string(4)
        meshType = self.inFile.readUInt()
        
        #header
        unk1, numStrings, count1, numMat, unk5, count2, \
            numFaceGroups, totalIndex, unk9 = self.inFile.read('9L')
        self.inFile.read('7f')
        for i in range(numStrings):
            self.read_name()
        self.inFile.read('%dL' %numStrings)
        self.inFile.read('%dL' %count1)
        self.parse_unk1(numMat)
        self.parse_unk2(count2)
        self.parse_face_info(numFaceGroups)
        self.parse_faces()
                
        #vertex section
        print(self.inFile.tell())
        vertType = self.inFile.readUInt()
        if vertType == 0:
            vertSize = 36
        elif vertType in [1, 4]:
            vertSize = 44
        elif vertType == 5:
            vertSize = 52
        else:
            print("unknown vertType", vertType)
        sectionSize = self.inFile.readUInt()
        print(self.inFile.tell())
        numVerts = sectionSize // vertSize
        self.parse_vertices(numVerts, vertType)
        
        self.inFile.readUInt()
        self.build_mesh(meshType)