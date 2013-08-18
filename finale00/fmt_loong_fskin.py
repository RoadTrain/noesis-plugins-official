from inc_noesis import *
import noesis
import rapi
import os

'''
MODE CONFIGURATION
0 = single model
1 = all models
'''
MODE = 0

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Loong", ".fskin")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    return 1

def load_all_models(mdlList):
    '''Load all models in the selected model's directory'''

    #carry over from previous models
    matList = []
    texList = []

    dirPath = rapi.getDirForFilePath(rapi.getInputName())
    fileList = [file for file in os.listdir(dirPath) if file.lower().endswith(".fskin")]
    for filename in fileList:
        f = open(dirPath + filename, 'rb')
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
    
    filename = rapi.getLocalFileName(rapi.getInputName())
    basename, ext = os.path.splitext(filename)    
    parser = SanaeParser(data)
    parser.parse_file(basename)
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
        self.idxBuffs = []
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []       
        
    def read_ustring(self, n):
               
        string = self.inFile.readBytes(n*2)
        return noeStrFromBytes(string, 'utf-16')

    def invert_faces(self):
        '''Negates the x-coord of all vertices in the mesh'''
        
        trans = NoeMat43((NoeVec3((-1, 0, 0)),
                         NoeVec3((0, 1, 0)),
                         NoeVec3((0, 0, 1)),
                         NoeVec3((0, 0, 0))))
        rapi.rpgSetTransform(trans)    
        
    def build_meshes(self, numSections):
        
        for i in range(numSections):
            idxBuff, numIdx = self.idxBuffs[i]
            matName = self.matList[i].name
            
            rapi.rpgSetMaterial(matName)
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)        
        
    def parse_vertices(self, numVerts, vertType):
        
        positions = bytes()
        normals = bytes()
        uv = bytes()
        
        for i in range(numVerts):
            positions = b''.join([positions,self.inFile.readBytes(12)])
            normals = b''.join([normals, self.inFile.readBytes(12)])
            self.inFile.read('8f')
            uv = b''.join([uv, self.inFile.readBytes(8)])
            
            count = self.inFile.readUInt()
            for i in range(count):
                self.inFile.readUInt()
                self.inFile.read('4f')
        
        rapi.rpgBindPositionBuffer(positions, noesis.RPGEODATA_FLOAT, 12)
        rapi.rpgBindNormalBuffer(normals, noesis.RPGEODATA_FLOAT, 12)
        rapi.rpgBindUV1Buffer(uv, noesis.RPGEODATA_FLOAT, 8)
        #vertBuff = self.inFile.readBytes(88*numVerts)
        #rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 88, 0)
        
        self.invert_faces()
        
    def parse_faces(self, numIdx):
        
        idxBuff = self.inFile.readBytes(2*numIdx)
        self.idxBuffs.append([idxBuff, numIdx])
        
    def parse_materials(self, numMat, filename):
        
        for i in range(numMat):
            matId = self.inFile.readUInt()
            self.inFile.read('17f')
            self.inFile.read('4b')
            texName = self.read_ustring(768)
            normName = self.read_ustring(528)
            matName = "%s[%d]" %(filename, matId)
            material = NoeMaterial(matName, texName)
            material.setNormalTexture(normName)
            self.matList.append(material)
        
    def parse_bones(self, numBones):
        
        for i in range(numBones):
            boneId = self.inFile.readUInt()
            matrix = self.inFile.read('16f')
        
    def parse_file(self, filename):
        '''Main parser method'''
        
        idstring = self.read_ustring(5)
        self.inFile.readUShort()
        vertType, numVerts, vertOfs, numFaceSect, faceOfs, numMat, matOfs = \
            self.inFile.read('7L')
        self.inFile.read('6f')
        self.inFile.seek(vertOfs)
        self.parse_vertices(numVerts, vertType)

        #face section start
        for i in range(numFaceSect):
            self.inFile.read('8L')
            numIdx = self.inFile.readUInt() * 3
            self.parse_faces(numIdx)
            
            #sections
            numSect = self.inFile.readUInt()
            for i in range(numSect):
                count = self.inFile.readUInt() * 3
                self.inFile.seek(count*2, 1)
                
            self.inFile.read('2L')
            numBones = self.inFile.readUInt()
            self.parse_bones(numBones)
            
        #material section start
        self.parse_materials(numMat, filename)       
        self.build_meshes(numFaceSect)
