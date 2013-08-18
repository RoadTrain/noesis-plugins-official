from inc_noesis import *
import noesis
import rapi
from Sanae3D.Sanae import SanaeObject
import os

MODE = 0

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Blade Chronicles", ".mdl;.mbn")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 4:
        return 0
    bs = NoeBitStream(data)
    try:
        idstring = bs.readString()
        if idstring not in ["mdl", "e"]:
            return 0
        return 1
    except:
        return 0

def load_all_models(mdlList):
    '''Load all models'''

    #carry over from previous models
    matList = []
    texList = []
    
    filename = rapi.getLocalFileName(rapi.getInputName())
    baseName = filename[:8]
    dirPath = rapi.getDirForFilePath(rapi.getInputName())
    fileList = [file for file in os.listdir(dirPath) if file.lower().endswith(".mdl")
                and baseName in file]
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
    
    if rapi.checkFileExt(rapi.getInputName(), ".mbn"):
        bs = NoeBitStream(data)
        idstring = bs.readUInt()
        numFiles = bs.readUInt()
        bs.read('2L')
        filesizes = []
        for i in range(numFiles):
            unk, size, crc, null = bs.read('4L')
            filesizes.append(size)
            
        for i in range(numFiles):
            size = filesizes[i]
            mdl = bs.readBytes(size)
            parser = mdl_parser(mdl)
            parser.parse_file()
            mdl = rapi.rpgConstructModel()
            mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
            mdlList.append(mdl)            
        
    elif rapi.checkFileExt(rapi.getInputName(), ".mdl"):
        parser = mdl_parser(data)
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

class mdl_parser(SanaeObject):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        super(mdl_parser, self).__init__(data)
        
    def parse_vertices(self, numVerts):
        
        vertBuff = self.inFile.readBytes(36*numVerts)
        rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 36, 0)
        rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 36, 12)
        rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 36, 28)      
       
    def parse_faces(self, numIdx):
       
        idxBuff = self.inFile.readBytes(2*numIdx)
        rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1) 
        
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.inFile.readString()
        self.inFile.read('3L')
        self.inFile.read('10f')
        self.inFile.read('2L')
        numVerts = self.inFile.readUInt()
        vertSize = self.inFile.readUInt()
        numIdx = self.inFile.readUInt()
        self.inFile.read('4L')
        
        self.parse_vertices(numVerts)
        self.parse_faces(numIdx)
        print(self.inFile.tell())