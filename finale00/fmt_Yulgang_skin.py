'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Yulgang (Scions of Fate)", ".skin")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    return 1

def noepyLoadModel(data, mdlList):
    '''Build the model, set materials, bones, and animations. You do not
    need all of them as long as they are empty lists (they are by default)'''
    
    ctx = rapi.rpgCreateContext()
    parser = SanaeParser(data)
    parser.parse_file()
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
    mdl.setBones(parser.boneList)
    mdl.setAnims(parser.animList)
    mdlList.append(mdl)
    return 1

class Mesh(object):
    
    def __init__(self):
        
        self.name = ""
        self.numIdx = 0
        self.numVerts = 0
        self.vertSize = 0
        self.idxBuff = bytes()
        self.vertBuff = bytes()

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
        self.vertType = -1
        self.basename = rapi.getExtensionlessName(rapi.getInputName())
        
    def build_mesh(self):
        
        for i in range(len(self.meshList)):
            mesh = self.meshList[i]
            rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 48, 0)
            rapi.rpgBindNormalBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 48, 28)
            rapi.rpgBindUV1BufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 48, 40)            
            
            matName = self.matList[i].name
            rapi.rpgSetMaterial(matName)
            rapi.rpgCommitTriangles(mesh.idxBuff, noesis.RPGEODATA_USHORT, mesh.numIdx, noesis.RPGEO_TRIANGLE, 1)
        
    def read_name(self):
        
        #string = self.inFile.readBytes(n)
        return noeStrFromBytes(string)
        
    def parse_materials(self, numMat):
            
        matName = "material"
        texName = self.basename + ".d2s"
        
        material = NoeMaterial(matName, texName)
        self.matList.append(material)
        
    def parse_textures(self, numTex):
            
        pass    
        
    def parse_vertices(self, numVerts):
        
        return self.inFile.readBytes(48*numVerts)
    
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(2*numIdx)
    
    def parse_bones(self, numBones):
        
        pass
        
    def parse_file(self):
        '''Main parser method'''
        
        self.inFile.readByte()
        
        mesh = Mesh()
        mesh.numVerts = self.inFile.readUInt()
        mesh.numIdx = self.inFile.readUInt() * 3
        
        self.inFile.readUInt()
        self.inFile.readUInt()
        
        self.inFile.read('6f')
        self.inFile.read("32f")
        mesh.vertBuff = self.parse_vertices(mesh.numVerts)
        mesh.idxBuff = self.parse_faces(mesh.numIdx)
        
        #unknowns after
        self.meshList.append(mesh)
        
        # no mat library?
        self.parse_materials(1)
        self.build_mesh()