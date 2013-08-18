from inc_noesis import *
import noesis
import rapi
from Sanae3D.Sanae import SanaeObject
import struct, os

MODE = 1

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Requiem Hurts", ".xm")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    return 1

def load_all_models(mdlList):
    '''Load all models'''

    #carry over from previous models
    matList = []
    texList = []

    dirPath = rapi.getDirForFilePath(rapi.getInputName())
    fileList = [file for file in os.listdir(dirPath) if file.lower().endswith(".xm")]
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
        self.textures = []
        
    def read_name(self):
        
        string = self.inFile.readBytes(64)
        try:
            return noeStrFromBytes(string)
        except:
            return ""
        
    def parse_textures(self):
        
        for i in range(len(self.textures)):
            texName, offset, texSize = self.textures[i]
            self.inFile.seek(offset)
            tex = tex = rapi.loadTexByHandler(self.inFile.readBytes(texSize), ".bmp")
            if tex is not None:
                tex.name = texName
                self.texList.append(tex)
    
    def parse_vertices(self, numVerts):
        
        vertBuff = self.inFile.readBytes(numVerts*32*3)
        rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 0)
        rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 12)
        rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 24)        
        
        idxBuff = bytes()
        for i in range(numVerts * 3):
            idxBuff += struct.pack('L', i)
            
        return idxBuff
    
    def parse_submesh(self, numSubmesh, matrix):
        
        for i in range(numSubmesh):
            matName = self.read_name()
            texName = self.read_name()
            texMask = self.read_name()
            numVerts, unk1, texSize, unk3, texOff, unk4, unk5 = self.inFile.read('7L')
            idxBuff = self.parse_vertices(numVerts)
            
            self.invert_faces()
            rapi.rpgSetMaterial(matName)
            rapi.rpgSetTransform(matrix)            
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_UINT, numVerts*3, noesis.RPGEO_TRIANGLE, 1)
            
            material = NoeMaterial(matName, texName)
            self.matList.append(material)
            
            if texName:
                self.textures.append([texName, texOff, texSize])
            
    def parse_mesh(self, numMesh):
        
        for i in range(numMesh):
            frameName = self.read_name()
            self.read_name()
            self.inFile.seek(256, 1)
            unk, numSubmesh, unk3, unk4 = self.inFile.read('4L')
            unk5, unk6, unk7, unk8 = self.inFile.read('4L')
            if not (unk5 and unk6 and unk7 and unk8):
                self.inFile.seek(120, 1)
            else:
                self.inFile.seek(104, 1)
            transform = self.inFile.readBytes(64)
            self.inFile.read('16f')
            self.inFile.read('16f')
            
            matrix = NoeMat44.fromBytes(transform).toMat43()


            self.parse_submesh(numSubmesh, matrix)
            
            
        
    def parse_file(self):
        '''Main parser method'''
        
        modelName = self.read_name()
        unk, numMesh = self.inFile.read('2L')
        self.parse_mesh(numMesh)
        self.parse_textures()