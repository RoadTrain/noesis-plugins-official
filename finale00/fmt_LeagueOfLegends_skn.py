from inc_noesis import *
import noesis
import rapi
import os

def registerNoesisTypes():
    '''Register the plugin'''
    
    handle = noesis.register("League of Legends", ".skn;.skl")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin.'''
    
    return 1

def noepyLoadModel(data, mdlList):
    '''Load the model'''
    
    ctx = rapi.rpgCreateContext()
    parser = SanaeParser(data)
    parser.parse_file()
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
    mdl.setBones(parser.boneList)
    mdl.setAnims(parser.animList)
    mdlList.append(mdl)
    return 1

class SklParser(object):
    
    def __init__(self, data):    
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        
    def read_name(self, n):
        
        return noeStrFromBytes(self.inFile.readBytes(n))
    
    def make_bone(self):
        
        pass
    
    def make_bone_parent(self):
        
        pass
    
    def make_bone_position(self):
        
        pass
        
    def parse_bones(self, numBones):
        
        for i in range(numBones):
            boneName = self.read_name(32)
            self.inFile.readUInt()
            self.inFile.readFloat()
            self.inFile.read('12f')
        
    def parse_file(self):
        
        idstring = self.read_name(8)
        self.inFile.readUInt()
        self.inFile.readUInt()
        numBones = self.inFile.readUInt()
        self.parse_bones(numBones)
        print(self.inFile.tell())

class SanaeParser(object):
    
    def __init__(self, data):    
        
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.dirpath = rapi.getDirForFilePath(rapi.getInputName())
        self.basename = rapi.getExtensionlessName(rapi.getInputName())
        
    def read_name(self, n):
        
        return noeStrFromBytes(self.inFile.readBytes(n))
    
    def parse_skeleton(self):
        
        sklFile = self.dirpath + self.basename + ".skl"
        f = open(sklFile, 'rb')
        skl = SklParser(f.read())
        f.close()
        
        skl.parse_file()
    
    def parse_vertices(self, numVerts):
        
        vertBuff = self.inFile.readBytes(52*numVerts)
        rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 52, 0)
        rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 52, 32)
        rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 52, 44)
    
    def parse_faces(self, numIdx, matName):
        
        return self.inFile.readBytes(numIdx*2)
    
    def get_texture_name(self):
        '''Search current directory for any texture that contains the
        basename of this file'''
    
        filename = os.path.basename(self.basename).lower()
        base_model = False
        if filename.find("_") == -1:
            filename_base = filename + "_base"
            base_model = True
        dirList = [file for file in os.listdir(self.dirpath) if file.lower().endswith(".dds")]
        
        for name in dirList:
            if base_model:
                if filename_base in name.lower():
                    return name
            if filename in name.lower():
                return name
        return ""
    
    def parse_texture(self):
        
        texName = self.get_texture_name()
        if texName:
            f = open(self.dirpath + texName, 'rb')
            tex = rapi.loadTexByHandler(f.read(), ".dds")
            f.close()
            if tex is not None:
                tex.name = texName
                self.texList.append(tex)
            return texName
        else:
            return ""
        
    def parse_material(self):
        
        matName = "material"
        
        texName = self.parse_texture()
        material = NoeMaterial(matName, texName)
        self.matList.append(material)
        return matName
        
    def parse_file(self):
        
        idstring = self.inFile.readUInt()
        hasMat, numMesh = self.inFile.read('2H')
        if hasMat:
            numMat = self.inFile.readUInt()
            for i in range(numMat):
                name = self.read_name(64)
                self.inFile.read('4L')
            
            #just hardcode matName for now
            matName = self.parse_material()
                
            numIdx = self.inFile.readUInt()
            numVerts = self.inFile.readUInt()
        else:
            matName = self.parse_material()
            numIdx, numVerts = self.inFile.read('2L')
        
        idxBuff = self.parse_faces(numIdx, matName)
        self.parse_vertices(numVerts)
        
        rapi.rpgSetMaterial(matName)
        rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
        
        #load skeleton
        #self.parse_skeleton()