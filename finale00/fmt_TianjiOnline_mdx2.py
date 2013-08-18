'''Noesis import plugin. Written by Tsukihime

Supports the following games with mdx2 format
-Tianji Online (v4)
-The Castle of Dawn (v4)
'''

from inc_noesis import *
import noesis
import rapi
import os

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Tianji Online", ".mdx2")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 8:
        return 0
    try:
        bs = NoeBitStream(data)
        idstring = noeStrFromBytes(bs.readBytes(4))
        version = bs.readUInt()
        if idstring != "vers" or version != 4:
            return 0
        return 1
    except:
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
    
    def __init(self):
        
        self.numVerts = 0
        self.numIdx = 0
        self.matNum = None
        self.vertBuff = bytes()
        self.normBuff = bytes()
        self.uvBuff = bytes()
        self.idxBuff = bytes()

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
        self.dirpath = rapi.getDirForFilePath(rapi.getInputName())
    
    def read_chunk(self):
        
        return noeStrFromBytes(self.inFile.readBytes(4))
        
    def read_name(self, n):
        
        string = self.inFile.readBytes(n)
        try:
            return noeStrFromBytes(string)
        except:
            return string
        
    def build_mesh(self):
        
        for mesh in self.meshList:
            
            rapi.rpgBindPositionBuffer(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 12)
            rapi.rpgBindNormalBuffer(mesh.normBuff, noesis.RPGEODATA_FLOAT, 12)
            rapi.rpgBindUV1Buffer(mesh.uvBuff, noesis.RPGEODATA_FLOAT, 8)            
            trans = NoeMat43((NoeVec3((1.0, 0.0, 0.0)), NoeVec3((0.0, 0.0, 1.0)), NoeVec3((0.0, 1.0, 0.0)), NoeVec3((0.0, 0.0, 0.0))))
            rapi.rpgSetTransform(trans)            
            
            matName = ""
            if mesh.matNum != -1:
                matName = self.matList[mesh.matNum].name
                
            rapi.rpgSetOption(noesis.RPGOPT_TRIWINDBACKWARD, 1)
            rapi.rpgSetMaterial(matName)
            rapi.rpgCommitTriangles(mesh.idxBuff, noesis.RPGEODATA_USHORT, mesh.numIdx, noesis.RPGEO_TRIANGLE, 1)
        
    def parse_material(self):
            
        count = len(self.matList)
        matName = "material[%d]" %count
        
        material = NoeMaterial(matName, "")
        material.setDefaultBlend(0)
        return material
    
    def parse_lays(self, material):
        
        self.inFile.read('3L')
        texNum = self.inFile.readUInt()
        self.inFile.readFloat()
        texName = self.texList[texNum].name
        material.setTexture(texName)
        self.matList.append(material)        
        
    def parse_textures(self, numTex):
        
        for i in range(numTex):
            texName = self.read_name(260)
            
            if not isinstance(texName, str):
                cut = texName.split(b'\x5C')
                if len(cut) > 1:
                    texName = noeStrFromBytes(cut[-1])
                else:
                    
                    texName = noeStrFromBytes(temp)
            
            try:
                texName = texName.replace('bmp', 'dds')
                filename, ext = os.path.splitext(texName)
                f = open(self.dirpath + texName, 'rb')
                tex = rapi.loadTexByHandler(f.read(), ext)
                if tex is not None:
                    tex.name = texName
                    self.texList.append(tex)
                else:
                    
                    tex = NoeTexture("dummy", 0, 0, 0, 0)
                    self.texList.append(tex)                    
            except:
                print("Couldn't find file: %s" %texName)
                tex = NoeTexture("dummy", 0, 0, 0, 0)
                self.texList.append(tex)
        
    def parse_vertices(self, numVerts):
        
        vertBuff = self.inFile.readBytes(numVerts*12)
        normBuff = self.inFile.readBytes(numVerts*12)
        uvBuff = self.inFile.readBytes(numVerts*8)
        return vertBuff, normBuff, uvBuff
    
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx*2)
    
    def parse_mesh(self):
        
        mesh = Mesh()
        numVerts = self.inFile.readUInt()
        numIdx = self.inFile.readUInt() * 3
        matNum = self.inFile.readInt()
        vertBuff, normBuff, uvBuff = self.parse_vertices(numVerts)
        self.inFile.seek(numVerts, 1)
        idxBuff = self.parse_faces(numIdx)
        
        mesh.numVerts = numVerts
        mesh.numIdx = numIdx        
        mesh.vertBuff = vertBuff
        mesh.normBuff = normBuff
        mesh.uvBuff = uvBuff
        mesh.idxBuff = idxBuff
        mesh.matNum = matNum
        
        self.meshList.append(mesh)
    
    def parse_bones(self, numBones):
        
        pass
    
    def parse_version(self):
        
        self.version = self.inFile.readUInt()
        
    def parse_file(self):
        '''Main parser method'''
        
        while self.inFile.tell() != self.inFile.dataSize:
            chunk = self.read_name(4)
            size = self.inFile.readUInt()
            
            if chunk == "vers":
                self.parse_version()
            elif chunk == "texs":
                numTex = self.inFile.readUInt()
                self.parse_textures(numTex)
            elif chunk == "mtls":
                pass
            elif chunk == "matl":
                material = self.parse_material()
            elif chunk == "lays":
                self.parse_lays(material)
            elif chunk == "geom":
                pass
            elif chunk == "chks":
                self.parse_mesh()
            else:
                self.inFile.seek(size, 1)
        self.build_mesh()