from inc_noesis import *
import noesis
import rapi
import os

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("LithTech", ".abc")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 8:
        return 0
    try:
        bs = NoeBitStream(data)
        length = bs.readUShort()
        idstring = noeStrFromBytes(bs.readBytes(length))
        if idstring != "Header":
            return 0
        return 1
    except:
        return 0

def noepyLoadModel(data, mdlList):
    '''Build the model, set materials, bones, and animations. You do not
    need all of them as long as they are empty lists (they are by default)'''
    
    inputName = rapi.getLocalFileName(rapi.getInputName())
    filename, ext = os.path.splitext(inputName)    
    ctx = rapi.rpgCreateContext()
    parser = SanaeParser(data, filename)
    parser.parse_file()
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
    mdl.setBones(parser.boneList)
    mdl.setAnims(parser.animList)
    mdlList.append(mdl)
    return 1

class LithTechNode(object):
    '''A LithTech node object'''
    
    def __init__(self):
        
        self.nodeName = ""
        self.offset = 0
        
class Mesh(object):
    
    def __init__(self):
        
        self.submeshes = []
        self.normList = []
        self.vertList = []
        self.uvList = []
        self.idxList = []
        self.meshName = ""
        self.numIdx = 0
        self.numVerts = 0

class SanaeParser(object):
    
    def __init__(self, data, filename):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.nodeList = []
        self.numMesh = 0
        self.numSubmesh = 0
        self.numBones = 0
        self.basename = filename
        self.meshList = []
        
    def read_name(self):
        
        string = self.inFile.readBytes(self.inFile.readUShort())
        return noeStrFromBytes(string)
    
    def build_vertices(self, mesh, meshName):
        
        vertBuff = bytes()
        normBuff = bytes()
        uvBuff = bytes()
        idxBuff = bytes()
        rapi.rpgSetName(meshName)
        for i in range(mesh.numIdx):
            index = mesh.idxList[i]
            vertBuff += struct.pack('3f', *mesh.vertList[index])
            normBuff += struct.pack('3f', *mesh.normList[index])
            uvBuff += struct.pack('2f', *mesh.uvList[i])
            idxBuff += struct.pack('H', i)
            
        rapi.rpgBindPositionBuffer(vertBuff, noesis.RPGEODATA_FLOAT, 12)
        rapi.rpgBindNormalBuffer(normBuff, noesis.RPGEODATA_FLOAT, 12)
        rapi.rpgBindUV1Buffer(uvBuff, noesis.RPGEODATA_FLOAT, 8)
        

        matName = meshName
        material = NoeMaterial(matName, self.basename)
        material.setDefaultBlend(0)
        self.matList.append(material)
        
        rapi.rpgSetMaterial(meshName)
        rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, mesh.numIdx, noesis.RPGEO_TRIANGLE, 1)
    
    def build_meshes(self):
        
        i = 0
        for mesh in self.meshList:
            for submesh in mesh.submeshes:
                meshName = "%s[%i]" %(mesh.meshName, i)
                self.build_vertices(submesh, meshName)
                i += 1
        
    def parse_vertices(self, numVerts, mesh):
         
        #vertBuff = bytes()
        #normBuff = bytes()
        vertList = []
        normList = []
        verts = 0
        for i in range(numVerts):
            count = self.inFile.readUShort()
            self.inFile.readUShort()
            for j in range(count):
                self.inFile.readUInt()
                self.inFile.read('4f')
            #vertBuff += self.inFile.readBytes(12)
            #normBuff += self.inFile.readBytes(12)
            vertList.append(self.inFile.read('3f'))
            normList.append(self.inFile.read('3f'))
        #rapi.rpgBindPositionBuffer(vertBuff, noesis.RPGEODATA_FLOAT, 12)
        #rapi.rpgBindNormalBuffer(normBuff, noesis.RPGEODATA_FLOAT, 12)
        
        mesh.numVerts = numVerts
        mesh.vertList = vertList
        mesh.normList = normList
    
    def parse_faces(self, numFaces, mesh):
        
        idxList = []
        uvList = []
        for i in range(numFaces):
            uvList.append(self.inFile.read('2f'))
            idxList.append(self.inFile.readUShort())
            uvList.append(self.inFile.read('2f'))
            idxList.append(self.inFile.readUShort())
            uvList.append(self.inFile.read('2f'))
            idxList.append(self.inFile.readUShort())
        
        mesh.numIdx = numFaces * 3
        mesh.idxList = idxList
        mesh.uvList = uvList
    
    def parse_bones(self):
        
        for i in range(self.numBones):
            boneName = self.read_name()
            self.inFile.readShort()
            self.inFile.readByte()
            matrix = self.inFile.read('16f')
            self.inFile.readUInt()
            
        count = self.inFile.readUInt() 
        for i in range(count):
            self.read_name()
            numBones = self.inFile.readUInt()
            self.inFile.seek(numBones*4, 1)
            
    def parse_meshes(self):
        
        self.inFile.read('2L')
        for i in range(self.numMesh):
            mesh = Mesh()
            self.inFile.readUShort()
            self.inFile.read('3f')
            self.inFile.readUShort()
            meshName = self.read_name()
            mesh.meshName = meshName
            for j in range(self.numSubmesh):
                submesh = Mesh()
                numFaces = self.inFile.readUInt()
                idxBuff = self.parse_faces(numFaces, submesh)
                numVerts = self.inFile.readUInt()
                self.parse_vertices(numVerts, submesh)
                mesh.submeshes.append(submesh)                
            self.meshList.append(mesh)
                
    def parse_header(self):
        
        #number of integers
        count = self.inFile.readUInt()
        self.inFile.read('2L')
        self.numBones = self.inFile.readUInt()
        self.numMesh = self.inFile.readUInt()
        self.inFile.read('4L')
        self.numSubmesh = self.inFile.readUInt()
    
    def parse_nodes(self):
        
        for node in self.nodeList:
            name = node.name
            offset = node.offset
            
            self.inFile.seek(offset)
            if name == "Header":
                self.parse_header()
            elif name == "Pieces":
                self.parse_meshes()
            elif name == "Nodes":
                self.parse_bones()
            elif name == "ChildModels":
                pass
            elif name == "Animation":
                pass
            elif name == "Sockets":
                pass
            elif name == "AnimBindings":
                pass
        
    def parse_file(self):
        
        offset = 0
        while offset != -1:
            self.inFile.seek(offset)
            node = LithTechNode()
            node.name = self.read_name()            
            self.nodeList.append(node)
            offset = self.inFile.readInt()
            
            #record the start of node data
            node.offset = self.inFile.tell()
            
        self.parse_nodes()
        self.build_meshes()