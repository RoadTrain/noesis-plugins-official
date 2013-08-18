'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi
import os

MODE = 1

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Cloud Nine", ".xskin")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 18:
        return 0
    try:
        bs = NoeBitStream(data)
        idstring = noeStrFromBytes(bs.readBytes(6))
        bs.readUInt()
        bs.readUShort()
        idstring2 = bs.readString()
        if idstring != "xbin\r\n" or idstring2 != "xSkin":
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
    fileList = [file for file in os.listdir(dirPath) if file.lower().endswith(".xskin")]
    for file in fileList:
        filename, ext = os.path.splitext(file)
        f = open(dirPath + file, 'rb')
        data2 = f.read()
        parser = SanaeParser(data2)
        parser.parse_file(filename)
        matList.extend(parser.matList)
        texList.extend(parser.texList)
        mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(texList, matList))
    mdlList.append(mdl)    
    
def load_single_model(data, mdlList):
    '''Loads a single model. For testing purposes'''
    
    filename, ext = os.path.splitext(rapi.getLocalFileName(rapi.getInputName()))
    parser = SanaeParser(data)
    parser.parse_file(filename)
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
        
        string = self.inFile.readBytes(self.inFile.readUShort())
        self.inFile.readByte()
        return noeStrFromBytes(string)
    
    def parse_vertices(self, numVerts):
        
        vertBuff = self.inFile.readBytes(numVerts*32)
        rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 0)
        rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 12)
        rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 24)
        
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx*2)
    
    def parse_material(self):
        
        dirpath = rapi.getDirForFilePath(rapi.getInputName())
        
        matName = self.read_name()
        self.inFile.readByte() #?
        self.inFile.read('17f')
                
        hasDiff = self.inFile.readUInt()
        if hasDiff:
            texPath = self.read_name()

        hasSpec = self.inFile.readUInt()
        if hasSpec:
            specPath = self.read_name()
        
        hasNorm = self.inFile.readUInt()
        if hasNorm:
            normPath = self.read_name()
        self.inFile.seek(7, 1)
        blend = self.read_name()
        
        texName = os.path.basename(texPath)
        tempPath = dirpath + "texture\\" + texName 
        material = NoeMaterial(matName, tempPath)
        material.setDefaultBlend(0)
        self.matList.append(material)
        return matName

    def parse_unk(self):
        
        unk = self.inFile.readInt()
        while unk != -1:
            unk = self.inFile.readInt()
            
    def parse_unk2(self, count):
        
        self.inFile.seek(count*12, 1)
        for i in range(count):
            self.inFile.readByte()
            self.inFile.readUInt()
            
    def parse_unk3(self, count):
        
        self.inFile.seek(count*12, 1)
        
    def parse_unk4(self, count):
        
        self.inFile.seek(count*12, 1)
        
    def parse_file(self, filename):
        
        idstring = self.inFile.readBytes(6)
        unk, numMesh = self.inFile.read('2H')
        self.read_name()
        modelName = self.read_name()
        self.inFile.readByte() #?
        self.inFile.read('6f')
        self.inFile.read('2L')
        numVerts, numIdx = self.inFile.read('2H')
        self.parse_vertices(numVerts)
        idxBuff = self.parse_faces(numIdx)
        matName = self.parse_material()
        
        rapi.rpgSetMaterial(matName)
        rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
        ##unknowns
        #self.parse_unk()
        #count = self.inFile.readUInt()
        #self.parse_unk2(count)
        #count2 = self.inFile.readUInt()
        #self.parse_unk3(count2)
        #count3 = self.inFile.readUInt()
        #self.parse_unk4(count3)
        
        
        