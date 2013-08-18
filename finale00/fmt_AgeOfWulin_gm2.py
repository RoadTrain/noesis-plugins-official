from inc_noesis import *
import noesis
import rapi
from Sanae3D.Sanae import SanaeObject
import os

MODE = 0

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Age of Wulin", ".gm2")
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
    fileList = [file for file in os.listdir(dirPath) if file.lower().endswith(".gm2")]
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
        self.meshes = []
        self.vertBuffs = []
        self.idxBuffs = []
        self.materials = []
        
    def read_name(self):
        
        return self.inFile.readString()
    
    def build_mesh(self, vertSize):
        
        for i in range(len(self.vertBuffs)):
            vertBuff, numVerts = self.vertBuffs[i]
            idxBuff, numIdx = self.idxBuffs[i]
            matName = self.materials[i]
            
            if vertSize == 36:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 36, 0)
                rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 36, 12)
                rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 36, 28)
            elif vertSize == 44:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 44, 0)
                rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 44, 12)
                rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 44, 36)
            rapi.rpgSetMaterial(matName)
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
    
    def parse_faces(self):
        
        for i in range(len(self.meshes)):
            numIdx = self.meshes[i][1] * 3
            idxBuff = self.inFile.readBytes(numIdx * 2)
            self.idxBuffs.append([idxBuff, numIdx])
    
    def parse_vertices(self, vertSize):
        
        for i in range(len(self.meshes)):
            numVerts = self.meshes[i][0]
            vertBuff = self.inFile.readBytes(vertSize*numVerts)
            self.vertBuffs.append([vertBuff, numVerts])
            
    def parse_materials(self, numMat):
        
        for i in range(numMat):
            matName = self.read_name()
            texName = self.read_name()
            unk = self.read_name()
            if not unk:
                meshName = self.read_name()
            else:
                meshName = unk
            #self.materials.append([meshName, matName, texName])
            self.materials.append(matName)
            #print(self.read_name())
         
            material = NoeMaterial(matName, texName)
            self.matList.append(material)
            
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.read_string(4)
        v1 = self.inFile.readUInt()
        v2 = self.inFile.readUInt()
        numName = self.inFile.readUInt()
        numMat = self.inFile.readUInt()
        numMesh = self.inFile.readUInt()
        v6 = self.inFile.readUInt()
        v7 = self.inFile.readUInt()
        v8 = self.inFile.readUInt()
        v9 = self.inFile.readUInt() #total faces
        v10 = self.inFile.readUInt()
        
        bboxMin = self.inFile.read('3f')
        bboxMax = self.inFile.read('3f')
        radius  = self.inFile.readFloat()
        
        #if numName % 4 == 0:
        self.parse_materials(numMat)
            
        self.inFile.readUInt()      
        if numMesh == numMat:
            self.inFile.read('%dL' %numMesh*4)
        else:
            self.inFile.read('%dL' %numMat*3)
        
        #loop?
        for i in range(numMesh): #numMat or v8
            self.inFile.read('2L')
            self.inFile.read('3f')
            self.inFile.read('6L')
            self.inFile.read('3l') # usually -1's
        #end loop
        totalVerts = 0
        for i in range(numMesh):
            self.inFile.read('3L')
            self.inFile.read('4f')
            self.inFile.readUInt() #null
            numFaces = self.inFile.readUInt() #numIdx for obj
            self.inFile.readUInt()
            numVerts = self.inFile.readUInt() #total verts
            self.inFile.seek(64, 1)
            #print("object %d, %d verts, %d faces" %(i, numVerts, numFaces))
            totalVerts += numVerts
            self.meshes.append([numVerts, numFaces])
        
        self.parse_faces()
        self.inFile.readUInt()
        sectSize = self.inFile.readUInt()
        vertSize = sectSize // totalVerts
        self.parse_vertices(vertSize)
        self.build_mesh(vertSize)
        
        #rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, totalVerts, noesis.RPGEO_POINTS, 1)
        #rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
        #self.plot_points(numVerts)