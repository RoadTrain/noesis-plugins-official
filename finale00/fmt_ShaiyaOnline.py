from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Shaiya Online", ".3DO;.3DC;.SMOD")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    filename = rapi.getLocalFileName(rapi.getInputName())
    if not ( rapi.checkFileExt(filename, '.3DO') or \
       rapi.checkFileExt(filename, '.3DC') or \
       rapi.checkFileExt(filename, '.SMOD')):
        return 0
    return 1

def get_type(data):
    
    filename = rapi.getLocalFileName(rapi.getInputName())
    if rapi.checkFileExt(filename, '.3DO'):
        return Shaiya3DO(data)
    elif rapi.checkFileExt(filename, '.3DC'):
        return Shaiya3DC(data)
    elif rapi.checkFileExt(filename, '.SMOD'):
        return ShaiyaSMOD(data)

def noepyLoadModel(data, mdlList):
    '''Build the model, set materials, bones, and animations. You do not
    need all of them as long as they are empty lists (they are by default)'''
    
    ctx = rapi.rpgCreateContext()
    parser = get_type(data)
    parser.parse_file()
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
    mdl.setBones(parser.boneList)
    mdl.setAnims(parser.animList)
    mdlList.append(mdl)
    return 1

def build_mesh(meshList):
    
    for mesh in meshList:
        
        if mesh.vertSize == 32:
            rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 32, 0)
            rapi.rpgBindNormalBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 32, 12)
            rapi.rpgBindUV1BufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 32, 24)
        elif mesh.vertSize == 36:
            rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 36, 0)
            rapi.rpgBindNormalBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 36, 12)
            rapi.rpgBindUV1BufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 36, 28)              
        
        rapi.rpgSetMaterial(mesh.matName)
        rapi.rpgCommitTriangles(mesh.idxBuff, noesis.RPGEODATA_USHORT, mesh.numIdx, noesis.RPGEO_TRIANGLE, 1)

class Mesh(object):
    
    def __init__(self):
        
        self.numVerts = 0
        self.numIdx = 0
        self.matName = ""
        self.vertBuff = bytes()
        self.idxBuff = bytes()
        self.vertSize = 0

class Shaiya3DO(object):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.meshList = []
        self.basename = rapi.getExtensionlessName(rapi.getInputName())
        self.matName = "material"
            
    def read_name(self):
        
        string = self.inFile.readBytes(self.inFile.readUInt())
        try:
            return noeStrFromBytes(string)
        except:
            return string
        
    def parse_vertices(self, numVerts):
        
        return self.inFile.readBytes(numVerts*32)
        
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(2 * numIdx)
    
    def parse_material(self, texName=""):
            
        if not texName:
            texName = self.basename + ".dds"
        material = NoeMaterial(self.matName, texName)
        self.matList.append(material)
        
    def parse_mesh(self, mesh):
        
        mesh.vertSize = 32
        mesh.numVerts = self.inFile.readUInt()
        mesh.vertBuff = self.parse_vertices(mesh.numVerts)
        mesh.numIdx = self.inFile.readUInt() * 3
        mesh.idxBuff = self.parse_faces(mesh.numIdx)
        
        
    def parse_file(self):
        '''Main parser method'''
        
        mesh = Mesh()
        texName = self.read_name()
        self.parse_mesh(mesh)
        self.parse_material()
        mesh.matName = self.matName
        self.meshList.append(mesh)
        
        build_mesh(self.meshList)
        
class Shaiya3DC(object):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.meshList = []
        self.basename = rapi.getExtensionlessName(rapi.getInputName())
        self.matName = "material"
        
    def parse_bones(self, numBones):
        
        for i in range(numBones):
            matrix = self.inFile.read('16f')
    
    def parse_vertices(self, numVerts):

        vertBuff = self.inFile.readBytes(numVerts*40)
        rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 40, 0)
        rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 40, 20)
        rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 40, 32)
    
    def parse_faces(self, numIdx):
        
        idxBuff = self.inFile.readBytes(numIdx*2)
        return idxBuff
    
    def parse_material(self):
        
        texName = self.basename + ".dds"
        material = NoeMaterial(self.matName, texName)
        self.matList.append(material)
        
    def parse_file(self):
        '''Main parser method'''
        
        self.inFile.readUInt()
        try:
            numBones = self.inFile.readUInt()
            self.parse_bones(numBones)
            numVerts = self.inFile.readUInt()
            self.parse_vertices(numVerts)
            numIdx = self.inFile.readUInt()*3
            idxBuff = self.parse_faces(numIdx)
            self.parse_material()
            rapi.rpgSetMaterial(self.matName)
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
        except:
            self.inFile.seek(4)
            numVerts = self.inFile.readUInt()
            self.parse_vertices(numVerts)
            numIdx = self.inFile.readUInt()*3
            idxBuff = self.parse_faces(numIdx)
            self.parse_material()
            rapi.rpgSetMaterial(self.matName)
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1) 
            
class ShaiyaSMOD(object):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.meshList = []
        self.basename = rapi.getExtensionlessName(rapi.getInputName())
        
    def read_name(self):
        
        string = self.inFile.readBytes(self.inFile.readUInt())
        try:
            return noeStrFromBytes(string)
        except:
            return string
    
    def parse_vertices(self, numVerts):
        
        return self.inFile.readBytes(numVerts*36)
        
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx*2)
        
    def parse_mesh(self, numMesh):
                
        for i in range(numMesh):
            mesh = Mesh()
            mesh.vertSize = 36
            mesh.matName = "material[%d]" %i
            mesh.texName = self.read_name()
            mesh.numVerts = self.inFile.readUInt()
            mesh.vertBuff = self.parse_vertices(mesh.numVerts)
            mesh.numIdx = self.inFile.readUInt() * 3
            mesh.idxBuff = self.parse_faces(mesh.numIdx)
            
            self.meshList.append(mesh)
            material = NoeMaterial(mesh.matName, mesh.texName)
            self.matList.append(material)
        
    def parse_file(self):
        '''Main parser method'''
        
        self.inFile.seek(40, 1)
        numMesh = self.inFile.readUInt()
        self.parse_mesh(numMesh)
        
        bboxMin = self.inFile.read('3f')
        bboxMax = self.inFile.read('3f')
        
        build_mesh(self.meshList)