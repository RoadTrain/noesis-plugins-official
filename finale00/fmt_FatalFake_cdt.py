from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin'''
    
    handle = noesis.register("Fatal Fake", ".cdt")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel) #see also noepyLoadModelRPG
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin.'''
    return 1

def noepyLoadModel(data, mdlList):
    '''Load the model'''
    
    ctx = rapi.rpgCreateContext()
    parser = FatalFake_CDT(data)
    parser.parse_file()
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
    mdlList.append(mdl)
    return 1

class FatalFake_CDT(object):
    
    def __init__(self, data):    
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
      
    def read_name(self):

        string = self.inFile.readBytes(self.inFile.readUShort())
        return noeStrFromBytes(string)
            
    def parse_unk1(self):
        
        count = self.inFile.readInt()
        self.inFile.read('%dL' %count)
        unk1 = self.inFile.readShort()
        if unk1 == 0:
            self.inFile.readFloat()
        else:
            self.parse_unk2()
            
    def parse_unk2(self):
        
        self.inFile.read('23B')
        numVerts = self.inFile.readInt()
        for i in range(numVerts):
            self.inFile.read("5f")
            self.inFile.readByte()
        count = self.inFile.readInt()
        for i in range(count):
            self.inFile.read('2L')
            self.inFile.read('8f')
        self.inFile.readByte()
        self.inFile.readFloat()
    
    def parse_vertices(self, numVerts):
         
        verts = self.inFile.readBytes(numVerts * 48)
        rapi.rpgBindPositionBufferOfs(verts, noesis.RPGEODATA_FLOAT, 48, 0)
        rapi.rpgBindNormalBufferOfs(verts, noesis.RPGEODATA_FLOAT, 48, 28)
        rapi.rpgBindUV1BufferOfs(verts, noesis.RPGEODATA_FLOAT, 48, 40)
        
        trans = NoeMat43((NoeVec3((-1, 0, 0)),
                         NoeVec3((0, 1, 0)),
                         NoeVec3((0, 0, 1)),
                         NoeVec3((0, 0, 0))))
        rapi.rpgSetTransform(trans)
            
    def parse_faces(self, numIdx):
        
        idxList = self.inFile.readBytes(numIdx * 2)
        return idxList
        
    def parse_face_section(self, numSects):
        
        for i in range(numSects):
            numIdx = self.inFile.readInt()
            idxList = self.parse_faces(numIdx)
            self.inFile.readInt()
            matName = self.read_name()
            
            rapi.rpgSetMaterial(matName)
            rapi.rpgCommitTriangles(idxList, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
            
    def parse_mesh(self, numMesh):
        
        for i in range(numMesh):
            meshName = self.read_name()
            rapi.rpgSetName(meshName)
            unk1, numVerts = self.inFile.read('2L')
            self.inFile.readByte()
            self.parse_vertices(numVerts)
            unk2, numSects = self.inFile.read('2L')
            self.parse_face_section(numSects)
            self.parse_unk1()
            
    def parse_materials(self, numMat):
        
        for i in range(numMat):
            self.inFile.read('16f')
            self.inFile.readUInt()
            matName = self.read_name()
            self.inFile.read('5L')
            numTex = self.inFile.readUInt()
            texNames = []
            for j in range(numTex):
                texNames.append(self.read_name())
                
            material = NoeMaterial(matName, "")
            material.setTexture(texNames[0] if texNames else "")
            self.matList.append(material)
            
    def parse_textures(self, numTex):
        
        for i in range(numTex):
            texName = self.read_name()
            texSize = self.inFile.readUInt()
            texData = self.inFile.readBytes(texSize)
            tex = rapi.loadTexByHandler(texData, ".dds")
            if tex is not None:
                tex.name = texName
                self.texList.append(tex)     
                
    def parse_bones(self, numBones):
        
        for i in range(numBones):
            boneName = self.read_name()
            frmName = self.read_name()
            self.inFile.read('35f')
            self.inFile.read('2L')
            
            print (boneName)
                
    def parse_file(self):
        self.inFile.read('2f')
        name = self.read_name()
        numMesh = self.inFile.readInt()
        self.inFile.readFloat()
        self.parse_mesh(numMesh)
        
        self.inFile.seek(-4, 1)
        #texture section
        numTex = self.inFile.readUInt()
        self.parse_textures(numTex)
        
        #material section
        numMat = self.inFile.readUInt()
        self.parse_materials(numMat)  
        
        self.inFile.readUInt()
        numBones = self.inFile.readUInt()
        #self.parse_bones(numBones)