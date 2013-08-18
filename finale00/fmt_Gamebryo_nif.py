from inc_noesis import *
import noesis
import rapi
from Sanae3D.Sanae import SanaeObject

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Gamebryo", ".nif")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 38:
        return 0
    try:
        bs = NoeBitStream(data)
        idstring = noeStrFromBytes(bs.readBytes(20))
        if idstring != "Gamebryo File Format":
            return 0
        return 1
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

class NifMesh(object):
    
    def __init__(self):
        
        self.numVerts = 0 
        self.numIdx = 0

class SanaeParser(SanaeObject):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        super(SanaeParser, self).__init__(data)
        self.idxBuffs = []
        self.vertBuffs = []
        
    def build_meshes(self):
        
        for i in range(len(self.vertBuffs)):
            idxBuff, numIdx, strips = self.idxBuffs[i]
            vertBuff, vertSize, numVerts =  self.vertBuffs[i]
            #render verts
            if vertSize == 12:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 12, 0)
            elif vertSize == 24:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 24, 0)
            elif vertSize == 32:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 0)
                rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 12)
            elif vertSize == 36:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 36, 0)
            elif vertSize == 40:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 40, 0)
            elif vertSize == 44:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 44, 0)
            elif vertSize == 48:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 48, 8)
            elif vertSize == 72:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 72, 0)
            elif vertSize == 76:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 76, 0)
            elif vertSize == 92:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 92, 20)
            self.plot_points(numVerts)
            #render faces
            if strips:
                #print("strips")
                rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
            else:
                #print("triangles")
                rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)                    
        
    def read_name(self):
        length = self.inFile.readUInt()
        string = self.inFile.readBytes(length)
        try:
            return noeStrFromBytes(string).strip()
        except:
            try:
                return noeStrFromBytes(string, "EUC-KR")
            except:
                print("unknown encode")
                return ""
            
    def parse_vertices(self, numVerts, vertSize):
        
        vertBuff = self.inFile.readBytes(numVerts*vertSize)
        self.vertBuffs.append([vertBuff, vertSize, numVerts])
        
    def parse_positions(self, numVerts):
        
        vertBuff = self.inFile.readBytes(numVerts*12)
        rapi.rpgBindPositionBuffer(vertBuff, noesis.RPGEODATA_FLOAT, 12)
        
    def parse_normals(self, numVerts):
        
        buff = self.inFile.readBytes(numVerts*12)
        rapi.rpgBindNormalBuffer(buff, noesis.RPGEODATA_FLOAT, 12)   
        
    def parse_vertex_colors(self, numVerts):
        
        buff = self.inFile.readBytes(numVerts*16)
        
    def parse_binormals(self, numVerts):
        
        buff = self.inFile.readBytes(numVerts*12)
        
    def parse_tangents(self, numVerts):
        
        buff = self.inFile.readBytes(numVerts*12)
            
    def parse_uv1(self, numVerts):
        
        buff = self.inFile.readBytes(numVerts*8)
        rapi.rpgBindUV1Buffer(buff, noesis.RPGEODATA_FLOAT, 8)
        
    def parse_uv2(self, numVerts):
    
        buff = self.inFile.readBytes(numVerts*8)
        rapi.rpgBindUV2Buffer(buff, noesis.RPGEODATA_FLOAT, 8)    
        
    def parse_faces(self, numIdx, strips=0):
       
        #print(numIdx, self.inFile.tell()) 
        idxBuff = self.inFile.readBytes(numIdx*2)
        self.idxBuffs.append([idxBuff, numIdx, strips])
        
        if strips:
            #print("strips")
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE_STRIP, 1)
        else:
            #print("triangles")
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)     
            
    def parse_NiMesh_part(self, count):
        
        self.f.write("%d %d\n" %(count, self.inFile.tell()))
        for i in range(count):
            chunkNum = self.inFile.readUInt()
            self.inFile.readByte()
            count2 = self.inFile.readUInt()
            self.inFile.read("%dH" %(count2 - 1))
            count3 = self.inFile.readUInt()
            for j in range(count3):
                self.inFile.read('2L')

    def parse_NiMesh(self):
        
        nodeNum = self.inFile.readUInt()
        self.inFile.read("2L")
        self.inFile.readUInt()
        self.inFile.readUShort()
        self.inFile.read('12f')
        count = self.inFile.readUInt()
        self.inFile.read('%dL' %count)
        self.inFile.read('5l') #-1 0 -1 0 ?
        self.inFile.read('4f')
        count2 = self.inFile.readUInt()
        self.parse_NiMesh_part(count2)
        
        
    def parse_NiTriStripsData(self):
        
        self.inFile.readUInt()
        numVerts = self.inFile.readUInt()
        flags = self.inFile.readUByte()
        self.parse_positions(numVerts)
        numUVSets, spaceFlag, hasNormals, = self.inFile.read('3B')
        if hasNormals:
            self.parse_normals(numVerts)
            if spaceFlag & 240:
                self.parse_binormals(numVerts)
                self.parse_tangents(numVerts)
        center = self.inFile.read('3f')
        radius = self.inFile.readFloat()
        hasVertColors = self.inFile.readUByte()
        if hasVertColors:
            self.parse_vertex_colors(numVerts)
        if numUVSets:
            self.parse_uv1(numVerts)
            if numUVSets == 2:
                self.parse_uv2(numVerts)
        self.inFile.readUShort()
        self.inFile.readInt() #-1?
        unk, unk = self.inFile.read('2H')
        numIdx = self.inFile.readUShort()
        self.inFile.readUByte()
        self.parse_faces(numIdx, strips=1)
        
    def parse_NiTriShapeData(self):
        
        self.inFile.readUInt()
        numVerts = self.inFile.readUInt()
        flags = self.inFile.readUByte()
        self.parse_positions(numVerts)
        numUVSets, spaceFlag, hasNormals, = self.inFile.read('3B')
        if hasNormals:
            self.parse_normals(numVerts)
            if spaceFlag & 240:
                self.parse_binormals(numVerts)
                self.parse_tangents(numVerts)
        center = self.inFile.read('3f')
        radius = self.inFile.readFloat()
        hasVertColors = self.inFile.readUByte()
        if hasVertColors:
            self.parse_vertex_colors(numVerts)
        if numUVSets:
            self.parse_uv1(numVerts)
            if numUVSets == 2:
                self.parse_uv2(numVerts)
        self.inFile.readUShort()
        self.inFile.readInt() #-1?
        numFaces, numIdx = self.inFile.read('2H')
        numStrips = self.inFile.readUShort()
        self.inFile.readUByte()
        self.parse_faces(numIdx)        
        
    def parse_NiTriStrips(self):
        
        nameID = self.inFile.readUInt()
        hasExtra = self.inFile.readUInt()
        
    def parse_NiDataStream118(self):
        
        size = self.inFile.readUInt()
        self.inFile.read('3L')
        numVerts = self.inFile.readUInt()
        count = self.inFile.readUInt()
        self.f.write("vertex parts: %d\n" %count)
        vertSize = 0
        vertTypes = []
        for i in range(count):
            data = self.inFile.readUInt()
            vertTypes.append(data)
            if data == 66069:
                vertSize += 2
            elif data == 262408:
                vertSize += 4
            elif data == 262416:
                vertSize += 4
            elif data == 197687:
                vertSize += 12
            elif data == 132150:
                vertSize += 8
        self.parse_vertices(numVerts, vertSize)
    
    def parse_NiDataStream018(self):
        
        size = self.inFile.readUInt()
        self.inFile.read('3L')
        numIdx = self.inFile.readUInt()
        self.inFile.read('2L')
        self.parse_faces(numIdx)
        
    def parse_NiDataStream33(self):
        
        self.inFile.read('4L')
        count = self.inFile.readUInt()
        self.inFile.read('2L')
        self.inFile.readBytes(count*2)
        self.inFile.readByte()
        
    def parse_nodes(self, numNodes):
        
        self.inFile.read('4B')
        offset = self.inFile.tell()
        for i in range(numNodes):
            self.inFile.seek(offset)
            nodeID = self.nodeIDs[i]
            size = self.sectionSizes[i]
            nodeName = self.sectionNames[nodeID].replace('\x01', '')
            self.f.write("%s %s\n" %(nodeName, offset))
            #print(nodeName, size)
            if nodeName == "NiNode":
                nodeNum = self.inFile.readUInt()
                self.f.write("%s\n" %nodeNum)
            elif nodeName == "NiMesh":
                self.parse_NiMesh()
            elif nodeName == "NiSourceTexture":
                self.inFile.readBytes(13)
                unk = self.inFile.readUInt()
            elif nodeName == "NiMaterialProperty":
                unk = self.inFile.readUInt()
            elif nodeName == "NiStringExtraData":
                self.inFile.readUInt()
                unk = self.inFile.readUInt()
            elif nodeName == "NiTriStrips":
                self.parse_NiTriStrips()
            elif nodeName == "NiTriStripsData":
                self.parse_NiTriStripsData()
            elif nodeName == "NiTriShapeData":
                self.parse_NiTriShapeData() 
            elif nodeName == "NiPixelData":
                pass
            elif nodeName in ["NiDataStream018"]:
                self.parse_NiDataStream018()
            elif nodeName in ["NiDataStream118"]:
                self.parse_NiDataStream118()     
            elif nodeName in ["NiDataStream33"]:
                self.parse_NiDataStream33()
            #else:
                #print(nodeName, self.inFile.tell())
            offset += size
        
    def parse_names(self):
            
        numNames, maxLen = self.inFile.read('2L')
        self.nodeSectionName = []
        for i in range(numNames):
            self.nodeSectionName.append(self.read_name())    

    def parse_header(self):
        
        idstring = self.read_string(39)
        self.version = self.inFile.readUInt()
        print(hex(self.version))
        
    def parse_chunks(self, numChunks, numNodes):
        
        self.sectionNames = []
        for i in range(numChunks):
            self.sectionNames.append(self.read_name())
        self.nodeIDs = self.inFile.read('%dH' %numNodes)
         
    def parse_file(self):
        '''Main parser method'''
        
        self.f = self.create_log('out.txt')
        self.parse_header()
        endian =self.inFile.readByte()
        userVersion = self.inFile.readUInt()
        numNodes = self.inFile.readUInt()
        numChunks = self.inFile.readUShort()
        self.parse_chunks(numChunks, numNodes)        
        if self.version == 0x14010003:
            self.parse_names()
            self.inFile.readUInt()
        elif self.version in [0x14010009, 0x14020007, 0x14020008, 0x14030009, 0x14060000]:
            self.sectionSizes = self.inFile.read('%dL' %numNodes)   
            self.parse_names()
            self.parse_nodes(numNodes)
            
        if self.version == 0x14060000:
            self.build_meshes()
            
        self.f.close()