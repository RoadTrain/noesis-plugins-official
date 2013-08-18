'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

'''For some reason, there are multiple copies of the mesh in one file, but you
don't need to load all of them. Set _LOAD_FIRST_MESH to True if you just want to
load the first one, False to load all'''

_LOAD_FIRST_MESH = True
_ENDIAN = 0 # 1 for big endian

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Waren Story", ".sobject")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 0:
        return 0
    try:
        bs = NoeBitStream(data)
        idstring = noeStrFromBytes(bs.readBytes(8))
        if idstring == "SOBJECT2":
            return 1
        return 0
    except:
        return 0

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

class SanaeParser(object):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data, _ENDIAN)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.meshList = []
        
        self.filename = rapi.getLocalFileName(rapi.getInputName())
        self.basename = rapi.getExtensionlessName(self.filename)
        
    def build_mesh(self):
        
        for i in range(len(self.meshList)):
            mesh = self.meshList[i]
            
            rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 76, 0)
            #rapi.rpgBindNormalBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 76, 56)
            rapi.rpgBindUV1BufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 76, 68) 
            
            #self.matList[0].setNormalTexture(self.texList[1].name)
            matName = self.matList[0].name
            rapi.rpgSetName(mesh.name)
            rapi.rpgSetMaterial(matName)
            rapi.rpgCommitTriangles(mesh.idxBuff, noesis.RPGEODATA_USHORT, mesh.numIdx, noesis.RPGEO_TRIANGLE, 1)
            
            if _LOAD_FIRST_MESH:
                break
        
    def read_name(self, n):
        
        string = self.inFile.readBytes(n)
        return noeStrFromBytes(string)
        
    def parse_vertices(self, numVerts):
        
        return self.inFile.readBytes(numVerts*76)
    
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx*2)
    
    def parse_unk(self, numVerts):
        
        self.inFile.readBytes(numVerts * 32)
        
    def parse_unk2(self, numIdx):
        
        self.inFile.readBytes(numIdx * 2)
    
    def parse_mesh(self, numMesh):
        
        for i in range(numMesh):
            mesh = Mesh()
            mesh.name = self.basename + "_%d" %i
            mesh.numVerts = self.inFile.readUInt()
            mesh.vertBuff = self.parse_vertices(mesh.numVerts)
            mesh.numIdx = self.inFile.readUInt() * 3
            mesh.idxBuff = self.parse_faces(mesh.numIdx)
            self.parse_unk(mesh.numVerts)
            self.parse_unk2(mesh.numIdx*2)
            self.meshList.append(mesh)
            
    def build_material(self, tex, name):
        
        matName = self.basename + "_%s" %name
        texName = self.basename + "_%s" %name
        tex.name = texName
        material = NoeMaterial(matName, texName)
        self.matList.append(material)
        self.texList.append(tex)
        
    def load_texture(self):
        size, zsize = self.inFile.read('2L')
        compData = self.inFile.readBytes(zsize)
        decompData = rapi.decompInflate(compData, size)
        tex = rapi.loadTexByHandler(decompData, ".dds")
        return tex
        
    def parse_textures(self):
        
        unk = self.inFile.readUInt()
        if unk:
            diffTex = self.load_texture()
            self.build_material(diffTex, "diff")
        unk = self.inFile.readUInt()
        if unk:
            normTex = self.load_texture()
            self.build_material(normTex, "norm")
        unk = self.inFile.readUInt()
        if unk:        
            specTex = self.load_texture() # specular?
            self.build_material(specTex, "spec")
                   
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.inFile.readBytes(8)
        type1, unk = self.inFile.read('2L')
        
        if self.basename.endswith("2") or type1 == 1:
            self.inFile.seek(372, 1)
            numMesh = self.inFile.readUInt()
            self.parse_mesh(numMesh)
            self.parse_textures()
            self.build_mesh()
        else:
            print("Unknown type: %d" %type1)
        