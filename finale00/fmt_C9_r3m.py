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
MODE = 1

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Continent of the 9", ".r3m")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 4:
        return 0
    try:
        bs = NoeBitStream(data)
        idstring = bs.readUInt()
        if idstring != 0:
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
    fileList = [file for file in os.listdir(dirPath) if file.lower().endswith(".r3m")]
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


class Mesh(object):
    
    def __init__(self):
        
        self.numVerts = 0
        self.numIdx = 0
        self.vertStart = 0
        self.idxStart = 0

class SanaeParser(object):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.meshList = []
        
    def read_name(self, n):
        
        string = self.inFile.readBytes(n)
        return noeStrFromBytes(string)
    
    def build_meshes(self, vertBuff, normBuff, uvBuff, idxBuff):
        
        for i in range(len(self.meshList)):
            mesh = self.meshList[i]
            vertStart = mesh.vertStart * 12
            vertEnd = vertStart + mesh.numVerts * 12
            uvStart = mesh.vertStart * 8
            uvEnd = uvStart + mesh.numVerts * 8
            idxStart = mesh.idxStart * 2
            idxEnd = idxStart + mesh.numIdx*2
            vBuff = vertBuff[vertStart:vertEnd]
            nBuff = normBuff[vertStart:vertEnd]
            uBuff = uvBuff[uvStart:uvEnd]
            iBuff = idxBuff[idxStart:idxEnd]
            
            rapi.rpgBindPositionBuffer(vBuff, noesis.RPGEODATA_FLOAT, 12)
            rapi.rpgBindNormalBuffer(nBuff, noesis.RPGEODATA_FLOAT, 12)
            rapi.rpgBindUV1Buffer(uBuff, noesis.RPGEODATA_FLOAT, 8)
            
            matName = self.matList[i].name
            rapi.rpgSetMaterial(matName)
            rapi.rpgCommitTriangles(iBuff, noesis.RPGEODATA_USHORT, mesh.numIdx, noesis.RPGEO_TRIANGLE, 1)        
        
    def parse_materials(self, numMat):
        
        for i in range(numMat):
            matName = "material[%d]" %i
            texName = self.inFile.readString()
            
            remain = 256 - len(texName) - 1
            self.inFile.seek(remain, 1)
            
            material = NoeMaterial(matName, texName)
            self.matList.append(material)
        
    def parse_textures(self, numTex):
            
        pass    
        
    def parse_vertices(self, numVerts):
        
        vertBuff = self.inFile.readBytes(numVerts*12)
        normBuff = self.inFile.readBytes(numVerts*12)
        uvBuff = self.inFile.readBytes(numVerts*8)
        self.inFile.readBytes(numVerts*24)
        return vertBuff, normBuff, uvBuff
    
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx*2)
    
    def parse_meshes(self, numMesh):
        
        #mesh header
        numVerts, numIdx = self.inFile.read('2L')
        for i in range(numMesh):
            mesh = Mesh()
            mesh.numVerts, mesh.numIdx, mesh.vertStart, mesh.idxStart = \
                self.inFile.read('4L')
            self.meshList.append(mesh)
        
        vertBuff, normBuff, uvBuff = self.parse_vertices(numVerts)
        idxBuff = self.parse_faces(numIdx)
        self.build_meshes(vertBuff, normBuff, uvBuff, idxBuff)
        
    
    def parse_bones(self, numBones):
        
        pass
        
    def parse_file(self, filename):
        '''Main parser method'''
        
        idstring = self.inFile.readBytes(4)
        numMat, unk = self.inFile.read('2L')
        self.inFile.read('6f')
        
        self.inFile.seek(1024)
        self.parse_materials(numMat)
        unk, numMesh = self.inFile.read('2L')
        self.parse_meshes(numMesh)