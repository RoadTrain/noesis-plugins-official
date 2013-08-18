'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi
import os

'''Loading configuration
0 = load only selected model
1 = load all models in the selected model's folder

You should only load all models if a model is separated into different files
'''
MODE = 0

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Continent of the 9", ".r3cm")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 4:
        return 0
    try:
        bs = NoeBitStream(data)
        idstring = bs.readBytes(4)
        if idstring != b'\xCD\xAB\xCD\xAB':
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
    fileList = [file for file in os.listdir(dirPath) if file.lower().endswith(".r3cm")]
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
        
    def read_name(self, n):
        
        string = self.inFile.readBytes(n)
        return noeStrFromBytes(string)
        
    def parse_materials(self, numMat):
            
        pass
        
    def parse_textures(self, numTex):
            
        pass    
        
    def parse_vertices(self, numVerts):
        
        vertBuff = self.inFile.readBytes(numVerts*40)
        rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 40, 0)
        rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_UINT, 40, 20)
        rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 40, 12)
    
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx*2)
    
    def parse_meshes(self, numMesh):
        
        pass
    
    def parse_bones(self, numBones):
        
        pass
        
    def parse_file(self, filename):
        '''Main parser method'''
        
        idstring = self.inFile.readBytes(4)
        self.inFile.read('3L')
        self.inFile.read('3f')
        self.inFile.readUInt()
        self.inFile.seek(1024)
        texName = self.inFile.readString()
        
        self.inFile.seek(1280)
        numVerts, numIdx = self.inFile.read('2L')
        self.parse_vertices(numVerts)
        idxBuff = self.parse_faces(numIdx)
        
        rapi.rpgSetMaterial(texName)
        rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)