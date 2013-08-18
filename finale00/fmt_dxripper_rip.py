'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi
import os

'''Load mode:
0 = selected model
1 = all models in folder
'''

MODE = 0

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("DX Ripper", ".rip")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 4:
        return 0
    bs = NoeBitStream(data)
    idstring = noeStrFromBytes(bs.readBytes(4))
    if idstring == "RUST":
        return 1
    return 0

def load_all_models(mdlList):
    '''Load all models'''

    #carry over from previous models
    matList = []
    texList = []

    dirPath = rapi.getDirForFilePath(rapi.getInputName())
    fileList = [file for file in os.listdir(dirPath) if file.lower().endswith(".rip")]
    for file in fileList:
        f = open(dirPath + file, 'rb')
        data2 = f.read()
        parser = SanaeParser(data2, file)
        parser.parse_file()
        matList.extend(parser.matList)
        texList.extend(parser.texList)
        mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(texList, matList))
    mdlList.append(mdl)    
    
def load_single_model(data, mdlList):
    '''Loads a single model. For testing purposes'''
    
    filename = rapi.getLocalFileName(rapi.getInputName())
    parser = SanaeParser(data, filename)
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

class Mesh(object):
    
    def initialize(self):
        
        self.numVerts = 0
        self.numIdx = 0
        self.vertBuff = bytes()
        self.idxBuff = bytes()

class SanaeParser(object):
    
    def __init__(self, data, name=""):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.meshList = []
        self.filename = name
        
    def build_mesh(self):
        
        for i in range(len(self.meshList)):
            mesh = self.meshList[i]
            rapi.rpgSetName(self.filename)
            rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 40, 0)
            rapi.rpgBindNormalBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 40, 16)
            rapi.rpgBindUV1BufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 40, 32)
    
            matName = self.matList[0].name
            rapi.rpgSetMaterial(matName)
            rapi.rpgCommitTriangles(mesh.idxBuff, noesis.RPGEODATA_UINT, mesh.numIdx, noesis.RPGEO_TRIANGLE, 1)
        
    def parse_textures(self):
        
        self.texNames = []
        for i in range(8):
            self.texNames.append(noeStrFromBytes(self.inFile.readBytes(16)))
            
    def parse_material(self):
        
        dif = self.inFile.read('4f')
        amb = self.inFile.read('4f')
        spe = self.inFile.read('4f')
        emi = self.inFile.read('4f')
        power = self.inFile.readFloat()
        
        material = NoeMaterial(self.filename, "")
        material.texName = self.texNames[0].split(".")[0]
        self.matList.append(material)
        
    def parse_shaders(self):
        
        for i in range(2):
            self.inFile.readBytes(16)
            
    def parse_vertices(self, numVerts):
        
        return self.inFile.readBytes(numVerts*40)
    
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx*4)
        
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.inFile.readBytes(4)
        headerSize = self.inFile.readUInt()
        
        mesh = Mesh()
        mesh.numVerts = self.inFile.readUInt()
        mesh.numIdx = self.inFile.readUInt() * 3
        self.parse_textures()
        self.parse_material()
        self.parse_shaders()
        mesh.vertBuff = self.parse_vertices(mesh.numVerts)
        mesh.idxBuff = self.parse_faces(mesh.numIdx)
        self.meshList.append(mesh)
        
        self.build_mesh()