'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi
import os

MODE = 0

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Touhou Maihana", ".geo")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 0:
        return 0
    bs = NoeBitStream(data)
    idstring = noeStrFromBytes(bs.readBytes(4))
    version = bs.readUInt()
    if idstring == "geo" and version == 4354:
        return 1
    return 0

def get_directory_path():
    
    dirPath = rapi.getDirForFilePath(rapi.getInputName())
    if not dirPath:
        dirPath = os.path.dirname(os.path.abspath(rapi.getInputName())) + "\\"
    return dirPath

def load_all_models(mdlList):
    '''Load all models'''

    #carry over from previous models
    matList = []
    texList = []

    dirPath = get_directory_path()
    fileList = [file for file in os.listdir(dirPath) if file.lower().endswith(".geo")]
    for file in fileList:
        filename, ext = os.path.splitext(file)
        f = open(dirPath + "\\" + file, 'rb')
        data2 = f.read()
        parser = SanaeParser(data2, filename)
        parser.parse_file()
        matList.extend(parser.matList)
        texList.extend(parser.texList)
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(texList, matList))
    mdlList.append(mdl)
    
def load_single_model(data, mdlList):
    '''Loads a single model. For testing purposes'''
    
    filename, ext = os.path.splitext(rapi.getLocalFileName(rapi.getInputName()))
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
    '''A generic mesh object, for convenience'''
    
    def __init__(self):
        
        self.vertBuff = bytes()
        self.normBuff = bytes()
        self.uvBuff = bytes()
        self.numVerts = 0
        self.numIdx = 0
        self.idxBuff = bytes()
        self.matName = ""
        self.meshName = ""

class SanaeParser(object):
    
    def __init__(self, data, filename):    
        
        self.inFile = NoeBitStream(data, 0)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.meshList = []
        self.filename = filename
        
    def build_mesh_imm(self):
        
        for i in range(len(self.meshList)):
            mesh = self.meshList[i]

            matName = self.matList[mesh.matNum].name
            rapi.rpgSetMaterial(matName)
            rapi.immBegin(noesis.RPGEO_TRIANGLE)
            for j in range(mesh.numFaces * 3):
                
                #idx = noeUnpackFrom("i", mesh.idxBuff, j*4)[0]
                #uvIdx = noeUnpackFrom("i", mesh.uvIdxBuff, j*4)[0]
                idx = mesh.idxList[j]
                uvIdx = mesh.uvIdxList[j]
                
                rapi.immNormal3f(mesh.normBuff, idx*12)
                rapi.immUV2f(mesh.uvBuff, uvIdx*8)
                rapi.immVertex3f(mesh.vertBuff, idx*12)
            rapi.immEnd()
            
    def read_name(self, n):
        
        string = self.inFile.readBytes(n)
        return noeStrFromBytes(string)
    
    def parse_materials(self, numMat):
        
        for i in range(numMat):
            matName = self.read_name(32)
            self.inFile.readUInt()
            self.inFile.read('4f')
            texNum = self.inFile.readInt()
            
            self.inFile.seek(524, 1)
            material = NoeMaterial(matName, "")
            if texNum != 255:
                texName = self.texList[texNum].name
                material.setTexture(texName)
            self.matList.append(material)
        
    def parse_textures(self, numTex, texInfo):
        
        for i in range(numTex):
            texOfs = texInfo[i]
            texSize = texInfo[i+1] - texOfs
            self.inFile.seek(texOfs)
            
            self.read_name(12)
            texName = self.read_name(32)
            width, height = self.inFile.read('2L')
            self.inFile.readUInt()
            self.inFile.read('2H')
            datSize = self.inFile.readUInt()
            data = self.inFile.readBytes(datSize)
            
            tex = rapi.loadTexByHandler(data, ".dds")
            if tex:
                tex.name = texName
                self.texList.append(tex)            
        
    def parse_vertices(self, numVerts, mesh):
        
        mesh.vertBuff = self.inFile.readBytes(numVerts*12)
        
    def parse_normals(self, numNorms, mesh):
        
        mesh.normBuff = self.inFile.readBytes(numNorms*12)
        
    def parse_uvs(self, numUV, mesh):
        
        mesh.uvBuff = self.inFile.readBytes(numUV * 8)
    
    def parse_faces(self, numFaces, mesh):
        
        #mesh.idxBuff = self.inFile.readBytes(numFaces * 12)
        #mesh.uvIdxBuff = self.inFile.readBytes(numFaces * 12)
        
        mesh.idxList = self.inFile.read('%dL' %numFaces*3)
        mesh.uvIdxList = self.inFile.read('%dL' %numFaces*3)
            
    def parse_unk(self, numFaces):
        
        self.inFile.seek(numFaces * 12, 1)
        
    def parse_unk2(self, count):
        
        for i in range(count):
            self.inFile.readUInt()
            count2 = self.inFile.readUInt()
            self.inFile.seek(count2 * 8, 1) # int, float
            
    def parse_unk3(self, count):
        '''Bunch of -1's'''
        
        self.inFile.seek(count*4, 1)
    
    def parse_meshes(self, numMesh):
        
        for i in range(numMesh):
            mesh = Mesh()
            
            meshName = self.read_name(64)
            flag1, numFaceGroups = self.inFile.read('2L')
            for i in range(numFaceGroups):
                numFaces, matNum = self.inFile.read('2L')
            mesh.matNum = matNum
            self.inFile.readUInt()
            self.inFile.read('2f')
            self.inFile.read('4l')
            mesh.numVerts, mesh.numNorms, mesh.numUV, unkCount1, \
                mesh.numFaces, unkCount2 = self.inFile.read('6L')
            self.inFile.read('16f')
            self.inFile.read('16f')
            
            if mesh.numVerts:
                self.parse_vertices(mesh.numVerts, mesh)
                self.parse_normals(mesh.numNorms, mesh)
                self.parse_uvs(mesh.numUV, mesh)
                
                self.parse_unk3(unkCount1)
                self.parse_faces(mesh.numFaces, mesh)
                self.parse_unk(mesh.numFaces)
                self.parse_unk2(unkCount2)                
            self.meshList.append(mesh)

        
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.inFile.readBytes(4)
        unk, unk, numMesh, numMat, numTex = self.inFile.read("5L")
        self.inFile.read('27f')
        self.inFile.readUInt()
        
        #tex offset and sizes
        texInfo = []
        for i in range(numTex + 1):
            texInfo.append(self.inFile.readUInt())
        
        matOfs = self.inFile.tell()
        self.parse_textures(numTex, texInfo)
        meshOfs = self.inFile.tell()

        self.inFile.seek(matOfs)
        self.parse_materials(numMat)
        
        self.inFile.seek(meshOfs)
        self.parse_meshes(numMesh)
        
        self.build_mesh_imm()