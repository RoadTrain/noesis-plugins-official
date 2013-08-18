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
    
    handle = noesis.register("Queen's Blade", ".mesh")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 4:
        return 0
    try:
        bs = NoeBitStream(data)
        idstring = bs.readFloat()
        idstring2 = bs.readInt()
        if idstring != 1 or idstring2 != 4:
            return 0
        return 1
    except:
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
    fileList = [file for file in os.listdir(dirPath) if file.lower().endswith(".mesh")]
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
        
        self.positions = bytes()
        self.normals = bytes()
        self.uvs = bytes()
        self.numVerts = 0
        self.numIdx = 0
        self.idxBuff = bytes()
        self.matName = ""
        self.meshName = ""

class MaterialParser(object):
    
    def __init__(self, data):
    
        self.inFile = NoeBitStream(data)
        self.matNames = []
        self.texNames = []
        
    def read_name(self, n):
        
        string = self.inFile.readBytes(n)
        try:
            return noeStrFromBytes(string)
        except:
            try: 
                return noeStrFromBytes(string, 'euc-kr')
            except:
                return "dummy"
    
    def parse_materials(self, numMat, filename):
        
        dirpath = rapi.getDirForFilePath(rapi.getInputName())
        for i in range(numMat):
            name = self.read_name(128)
            self.matName = self.read_name(128)
            if not self.matName:
                self.matName = "material[%d]" %i
            self.inFile.seek(56, 1)
            
            flag = self.inFile.readUInt()
            if flag in [37524, 45716]:
                self.texName = filename + ".dds"
                self.inFile.seek(252, 1)
            else:
                self.inFile.seek(-4, 1)
                try:
                    texPath = self.read_name(256)
                    self.texName = os.path.basename(texPath)            
                except:
                    self.texName = filename + ".dds"
            self.matNames.append(self.matName)
            self.texNames.append(dirpath + "texture\\" + self.texName)
        
    def parse_file(self, filename):
        
        self.inFile.readFloat()
        self.inFile.read('9L')
        self.inFile.readFloat()
        numMat = self.inFile.readUInt()
        self.parse_materials(numMat, filename)
        
class SanaeParser(object):
    
    def __init__(self, data, filename):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []        
        self.filename = filename
        self.meshList = []
        
    def build_mesh(self):
        
        for mesh in self.meshList:
            rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 92, 0)
            rapi.rpgBindNormalBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 92, 12)
            rapi.rpgBindUV1BufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 92, 28)                        
            rapi.rpgSetName(mesh.meshName)

            matName = self.matList[mesh.matNum].name
            rapi.rpgSetMaterial(matName)
            rapi.rpgCommitTriangles(mesh.idxBuff, noesis.RPGEODATA_UINT, mesh.numIdx, noesis.RPGEO_TRIANGLE, 1)
            
        
    def read_name(self, n):
        
        string = self.inFile.readBytes(n)
        try:
            return noeStrFromBytes(string)
        except:
            return "dummy"
    
    def parse_vertices(self, numVerts, mesh):
        
        vertBuff = self.inFile.readBytes(92 * numVerts)
        mesh.vertBuff = vertBuff       
        
    def parse_faces(self, numIdx, mesh):
        
        idxBuff = self.inFile.readBytes(numIdx*4)
        mesh.idxBuff = idxBuff
        
    def parse_materials(self):
        
        dirPath = rapi.getDirForFilePath(rapi.getInputName())
        matLib = self.filename + ".mtl"
        f = open(dirPath + matLib, 'rb')
        mat = MaterialParser(f.read())
        mat.parse_file(self.filename)
        
        numMat = len(mat.matNames)
        for i in range(numMat):
            matName, texName = mat.matNames[i], mat.texNames[i]
            material = NoeMaterial(matName, texName)
            self.matList.append(material)            
        
    def parse_mesh(self, numMesh):
        
        for i in range(numMesh):
            mesh = Mesh()
            mesh.numVerts = self.inFile.readUInt()
            self.parse_vertices(mesh.numVerts, mesh)
            mesh.numIdx = self.inFile.readUInt() * 3
            self.parse_faces(mesh.numIdx, mesh)
            mesh.matNum = self.inFile.readUInt()
            mesh.meshName = self.read_name(64)
            matName = self.read_name(128)
            self.read_name(128)
            self.inFile.read('3L')

            self.meshList.append(mesh)
            
    def parse_frames(self, numFrames):
        
        for i in range(numFrames):
            self.read_name(128)
            self.read_name(128)
            self.inFile.read('31f')        
            
    def parse_bones(self, numBones):
        
        for i in range(numBones):
            boneName = self.read_name(64)

    def parse_file(self):
        '''Main parser method'''
        
        self.parse_materials()
        
        idstring = self.inFile.readFloat()
        self.inFile.read('17L')
        self.inFile.readFloat()
        numFrames, numMesh, unk, unk = self.inFile.read('4L')
        self.parse_frames(numFrames)
        self.parse_mesh(numMesh)
        
        numBones = self.inFile.readUInt()
        #self.parse_bones(numBones)
        self.build_mesh()