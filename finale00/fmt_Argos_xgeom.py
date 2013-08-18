'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi
import os

MODE = 1

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Argos Online", ".xgeom")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 6:
        return 0
    try:
        bs = NoeBitStream(data)
        idstring = noeStrFromBytes(bs.readBytes(6))
        if idstring != "xbin\r\n":
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
    fileList = [file for file in os.listdir(dirPath) if file.lower().endswith(".xgeom")]
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

class MatLibrary(object):
    
    def __init__(self, data):
        
        self.inFile = NoeBitStream(data)
        
    def read_name(self):
        
        string = self.inFile.readBytes(self.inFile.readUShort())
        self.inFile.readByte()
        return noeStrFromBytes(string)
        
    def parse_file(self):
        
        dirpath = rapi.getDirForFilePath(rapi.getInputName())
        idstring = self.inFile.readBytes(6)
        self.inFile.readBytes(8)
        
        matName = self.read_name()
        self.inFile.seek(9, 1)
        self.read_name()
        self.inFile.seek(217, 1)
        label = self.read_name()
        self.inFile.readFloat()
        texName = self.read_name()
        
        texPath = dirpath + texName
        material = NoeMaterial(matName, texPath)
        return material

class SanaeParser(object):
    
    def __init__(self, data):    
        
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        
    def read_name(self):
        
        string = self.inFile.readBytes(self.inFile.readUShort())
        self.inFile.readByte()
        return noeStrFromBytes(string)
    
    def parse_vertices(self, numVerts, vertType):
        
        if vertType == 1:
            vertBuff = self.inFile.readBytes(numVerts*32)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 0)
            rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 12)
            rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 24) 
        elif vertType == 2:
            vertBuff = self.inFile.readBytes(numVerts*56)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 56, 0)
            rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 56, 12)
            rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 56, 24)
        elif vertType == 3:
            vertBuff = self.inFile.readBytes(numVerts*48)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 48, 0)
            rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 48, 12)
            rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 48, 24)
        else:
            print("unknown vertex type: %d" %vertType)
            
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx*2)
    
    def parse_material(self, matLib):
        
        dirpath = rapi.getDirForFilePath(rapi.getInputName())
        matLib = os.path.basename(matLib)
        matPath = dirpath + matLib
        
        try:
            f = open(matPath, 'rb')
            data = f.read()
            matLib = MatLibrary(data)
            material = matLib.parse_file()
            self.matList.append(material)
            return material.name
        except:
            print("Couldn't find file: ", matLib)
            return ""
            
    def parse_file(self, filename):
        '''Main parser method'''
        
        idstring = self.inFile.readBytes(6)
        self.inFile.read('4H')
        meshName = self.read_name()
        self.inFile.seek(9, 1)
        self.read_name()
        unk, vertType, type2, null = self.inFile.read('4B')
        self.inFile.readUInt()
        numVerts, numIdx = self.inFile.read('2H')
        self.parse_vertices(numVerts, vertType)
        idxBuff = self.parse_faces(numIdx)
        self.inFile.readUShort()
        matLib = self.read_name()
        matName = self.parse_material(matLib)
        
        rapi.rpgSetMaterial(matName)
        rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)