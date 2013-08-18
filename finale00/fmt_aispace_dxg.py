'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Aispace", ".dxg")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    bs = NoeBitStream(data)
    idstring = noeStrFromBytes(bs.readBytes(4))
    if idstring == "DXG ":
        return 1
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
    
    def __init__(self):
        
        self.name = ""
        self.numIdx = 0
        self.numVerts = 0
        self.vertSize = 0
        self.idxBuff = bytes()
        self.vertBuff = bytes()
        self.normBuff = bytes()
        self.uvBuff = bytes()

class SanaeParser(object):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.basename = rapi.getExtensionlessName(rapi.getLocalFileName(rapi.getInputName()))
        
    def build_mesh(self, mesh):
        
        vertBuff = bytes()
        normBuff = bytes()
        uvBuff = bytes()
        for i in range(mesh.numVerts):
            posIdx, normIdx, uvIdx = mesh.posList[i], mesh.normList[i], mesh.uvList[i]
            vertBuff = b''.join([vertBuff, mesh.vertBuff[posIdx * 12 : (posIdx+1) * 12]])
            normBuff = b''.join([normBuff, mesh.normBuff[normIdx * 12 : (normIdx+1) * 12]])
            uvBuff = b''.join([uvBuff, mesh.uvBuff[uvIdx * 8 : (uvIdx+1) * 8]])
            
        rapi.rpgBindPositionBuffer(vertBuff, noesis.RPGEODATA_FLOAT, 12)
        rapi.rpgBindNormalBuffer(normBuff, noesis.RPGEODATA_FLOAT, 12)
        rapi.rpgBindUV1Buffer(uvBuff, noesis.RPGEODATA_FLOAT, 8)
        #rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, mesh.numVerts, noesis.RPGEO_POINTS, 1)
        
        numIdx = mesh.numFaces * 3
        matName = self.matList[0].name
        rapi.rpgSetMaterial(matName)
        rapi.rpgCommitTriangles(mesh.idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
        
    def read_name(self):
        
        string = self.inFile.readBytes(self.inFile.readUInt())
        return noeStrFromBytes(string, "shift-jis")
        
    def build_material(self):
        
        matName = "material"    
        texName = self.basename.replace("EM", "ET")
        material = NoeMaterial(matName, texName + "0.dds")
        self.matList.append(material)
        
    def parse_textures(self, numTex):
            
        pass    
        
    def parse_vertices(self, numVerts):
        
        pass
    
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx * 2)
    
    def parse_meshes(self, numMesh):
        
        pass
    
    def parse_indices(self, numVerts, mesh):
        
        posList = []
        normList = []
        uvList = []
        
        for i in range(numVerts):
            posList.append(self.inFile.readShort())
            normList.append(self.inFile.readShort())
            uvList.append(self.inFile.readShort())
            self.inFile.read("2H")
            
        mesh.posList = posList
        mesh.normList = normList
        mesh.uvList = uvList
        
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.inFile.readBytes(4)
        self.inFile.read('2H')
        self.inFile.read('3L')
        mesh = Mesh()
        meshName = self.read_name()
        
        self.inFile.read('4L')
        meshSize = self.inFile.readUInt()
        numCoords, numNorms, numUV, null = self.inFile.read('4H')
        self.inFile.read('2L')
        mesh.numVerts, mesh.numFaces = self.inFile.read('2H')
        self.inFile.read('2L')
        sectionSize = self.inFile.readUInt()
        
        #indices
        self.parse_indices(mesh.numVerts, mesh)
        mesh.idxBuff = self.parse_faces(mesh.numFaces * 3)
        mesh.vertBuff = self.inFile.readBytes(numCoords * 12)
        mesh.normBuff = self.inFile.readBytes(numNorms * 12)
        mesh.uvBuff = self.inFile.readBytes(numUV * 8)
        
        self.inFile.readInt() #eof
        
        self.build_material()
        self.build_mesh(mesh)