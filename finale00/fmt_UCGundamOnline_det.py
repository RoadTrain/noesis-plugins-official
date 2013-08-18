'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi
import struct

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("UC Gundam Online", ".det")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 4:
        return 0
    bs = NoeBitStream(data)
    version = bs.readUShort()
    if version not in [2, 3, 4]:
        return 0
    return 1

def noepyLoadModel(data, mdlList):
    '''Build the model, set materials, bones, and animations. You do not
    need all of them as long as they are empty lists (they are by default)'''
    
    ctx = rapi.rpgCreateContext()
    parser = get_parser(data)
    parser.parse_file()
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
    mdl.setBones(parser.boneList)
    mdl.setAnims(parser.animList)
    mdlList.append(mdl)
    return 1

def get_parser(data):
    
    bs = NoeBitStream(data)
    version = bs.readShort()
    if version == 2:
        return Parser2(data)
    elif version == 3:
        return Parser3(data)
    elif version == 4:
        return Parser4(data)

class Mesh(object):
    
    def __init__(self):
        
        self.name = ""
        self.idxStart = 0
        self.numIdx = 0
        self.vertStart = 0
        self.numVerts = 0
        self.vertSize = 0
        self.idxBuff = bytes()
        self.vertBuff = bytes()
        self.submeshes = []
        
class Header(object):
    
    def __init__(self):
        
        self.version = 0
        self.vertChunks = 0
        self.faceChunks = 0
        self.scriptChunks = 0
        self.shaderChunks = 0
        self.matChunks = 0
        self.texChunks = 0
        
class UCGOParser(object):
    '''This class contains methods for parsing each struct that is common
    amongst version 1, 3, and 4 formats'''
    
    def __init__(self, data):    
        
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.meshList = []
        self.vertInfo = []
        self.idxInfo = []
        
    def make_transform(self, mesh):
        
        pass
        
    def build_meshes(self):
            
        rapi.rpgSetOption(noesis.RPGOPT_TRIWINDBACKWARD, 1)
        for i in range(len(self.meshList)):
            mesh = self.meshList[i]        
            rapi.rpgSetName(mesh.name)
            if mesh.vertSize == 32:
                rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 32, 0)
                rapi.rpgBindNormalBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 32, 12)
                rapi.rpgBindUV1BufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 32, 24)
            elif mesh.vertSize == 40:
                rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 40, 0)
                rapi.rpgBindNormalBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 40, 20)
                rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 40, 32)
            elif mesh.vertSize == 48:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 48, 0)
                rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 48, 28)
                rapi.rpgBindUV1BufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 48, 40)
                            
            for sub in mesh.submeshes:            
                idxStart = sub.idxOfs
                idxEnd = idxStart + sub.numIdx * 2
                idxBuff = mesh.idxBuff[idxStart:idxEnd]
            
                rapi.rpgSetMaterial(self.tex)
                rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, sub.numIdx, noesis.RPGEO_TRIANGLE, 1)
        
    def read_name(self):
            
        string = self.inFile.readBytes(self.inFile.readUInt())
        return noeStrFromBytes(string)
    
    def read_uname(self):
        
        string = self.inFile.readBytes(self.inFile.readUInt() * 2)
        return noeStrFromBytes(string, 'utf-16')
    
    def parse_header(self):
        
        header = Header()
        header.version = self.inFile.readShort()
        self.inFile.readShort()
        self.inFile.read('2H')
        unk = self.inFile.readUInt()
        header.vertChunks = self.inFile.readUInt()
        header.faceChunks = self.inFile.readUInt()
        header.scriptChunks = self.inFile.readUInt()
        header.shaderChunks = self.inFile.readUInt() - 1
        self.inFile.read("2L")
        header.matChunks = self.inFile.readUInt()
        header.texChunks = self.inFile.readUInt()
        
        if header.version == 4:
            self.inFile.readUInt()               
        return header
        
    def parse_vertices(self, vertChunks):
            
        #32, 40, 48
        for i in range(vertChunks):
            chunkID = self.inFile.readUShort()
            self.inFile.read('3H')
            chunkType = self.inFile.readUInt()
            size = self.inFile.readUInt()
            vertSize = self.inFile.readUInt()
            numVerts = self.inFile.readUInt()
            self.inFile.read("3L")
            vertBuff = self.inFile.readBytes(numVerts*vertSize)
            self.vertInfo.append([numVerts, vertSize, vertBuff])
            
    def parse_faces(self, faceChunks):
        
        for i in range(faceChunks):
            chunkID = self.inFile.readUShort()
            self.inFile.read('3H')
            chunkType = self.inFile.readUInt()        
    
            size = self.inFile.readUInt()
            idxSize = self.inFile.readUInt()
            numIdx = self.inFile.readUInt()
            self.inFile.read("3L")        
            idxBuff = self.inFile.readBytes(numIdx * 2)
            
            self.idxInfo.append([numIdx, idxBuff])
        
    def parse_scripts(self, scriptChunks):
        '''brute force skip'''
        
        for i in range(scriptChunks):
            self.inFile.read('4H')
            self.read_uname()
            
            t = self.inFile.readUShort()
            self.inFile.read("2H")
            while t != 0x5258:
                t = self.inFile.readUShort()
            self.inFile.seek(-8, 1)
            
    def parse_shader_fields(self, numFields):
        
        
            fieldName = self.read_name()
            size = self.inFile.readUInt()
            self.inFile.readUInt()
            self.inFile.readBytes(size)
            
    def parse_shader_chunks(self, shaderChunks):
        
        for i in range(shaderChunks):
            self.inFile.read('4H')
            self.inFile.readUInt()
            
            #shader?
            self.inFile.read('2H')
            shaderName = self.read_uname() #shader filename
            numFields = self.inFile.readUInt()
            
            for i in range(numFields):
                size = self.inFile.readUInt()
                self.inFile.readUInt()
                self.inFile.readBytes(size)
                fieldName = self.read_name()
            self.inFile.seek(740, 1)
    
    def parse_material(self):
        '''Data for the material object'''
        
        pass
            
    def parse_material_chunks(self, matChunks):
        ''' '''
        for i in range(matChunks):
            self.inFile.read('2H')
            self.inFile.read('2H')
            matName = self.read_uname()
            self.parse_material()
            
    def parse_texture(self):
                
        pass

    def parse_texture_chunks(self, texChunks):
        
        for i in range(texChunks):
            self.inFile.read('2H')
            self.inFile.read('2H')
            texName = self.read_uname()
            self.parse_texture()
            
            self.tex = texName
        
    def parse_bone_chunk(self):
        '''Contained inside the mesh'''
        
        self.inFile.read('2H')
        self.inFile.read('2H')
        self.inFile.read('4l')
        boneName = self.read_uname()
        print(boneName)
        
        # skip chunk after bone name
        self.inFile.seek(248, 1)
        
    def parse_empty_chunk(self):
        '''This seems empty, but it has a variable data length so
        we need to treat it as such'''
        
        self.inFile.read('2L')
        size = self.inFile.readUInt()
        self.inFile.readUInt()
        self.inFile.readBytes(size)
        #self.inFile.readUInt()
        
    def parse_frame_chunks(self, frameChunks):
        '''Chunk including the SCENE ROOT. Seems to hold information
        regarding mesh counts and frame counts and other things'''
        
        for i in range(frameChunks):
            meshType, xr = self.inFile.read('2H') #2, 3, 6 or 7
            if meshType == 2:
                self.inFile.seek(164, 1)
                self.parse_empty_chunk()
                self.read_uname()
            elif meshType == 3:
                self.inFile.seek(108, 1)
                unk1 = self.inFile.readUInt() # 0 or 4
                self.inFile.seek(56, 1)
                self.parse_empty_chunk()
                self.read_uname()
            elif meshType == 6:
                self.inFile.seek(156, 1)
                self.parse_empty_chunk()
                self.inFile.readUInt()
                root = self.read_uname() #scene root
            elif meshType == 7:
                self.inFile.seek(112, 1)
                unk1 = self.inFile.readUInt() # 0 or 4
                if unk1 == 0:
                    self.inFile.read('8f')
                elif unk1 == 4:
                    self.inFile.read('16f')
                self.inFile.read('2L')
                self.parse_empty_chunk()
                self.inFile.readUInt()
                root = self.read_uname() #scene root
         
    def parse_submesh_chunk(self, count, mesh):
        ''' This is inside the mesh. Occurs variable times. Submesh info?'''
        
        submeshes = []
        for i in range(count):
            submesh = Mesh()
            ctype, xr = self.inFile.read('2H') # 01, 02
            if ctype == 1:
                self.inFile.seek(28, 1)        
            elif ctype == 2:
                self.inFile.seek(16, 1)
                submesh.matNum = self.inFile.readUInt()
                self.inFile.seek(12, 1)
            self.inFile.read('2H')
            self.inFile.readUInt()
            submesh.idxStart = self.inFile.readUInt() * 3
            submesh.numIdx = self.inFile.readUInt() * 3
            submesh.idxOfs = self.inFile.readUInt() * 2
            submesh.vertStart = self.inFile.readUInt()
            submesh.numVerts = self.inFile.readUInt()
            self.inFile.readUInt()
            submeshes.append(submesh)    
        
        self.inFile.read("%dL" %count)
        self.inFile.read('2L')
        
        vertInfo = self.vertInfo[self.inFile.readUInt()]
        idxInfo = self.idxInfo[self.inFile.readUInt()]
        mesh.numVerts = vertInfo[0]
        mesh.vertSize = vertInfo[1]
        mesh.vertBuff = vertInfo[2]
        mesh.numIdx = idxInfo[0]
        mesh.idxBuff = idxInfo[1]
        self.inFile.read('3L')
        
        mesh.submeshes = submeshes
        
    def parse_mesh_chunks(self, meshChunks):
        
        for i in range(meshChunks):
            mesh = Mesh()
            chunkType, xr = self.inFile.read('2H')
            if chunkType == 2:
                self.inFile.seek(56, 1)
                count, count2 = self.inFile.read('2L')
                self.inFile.seek(4, 1)
                self.parse_submesh_chunk(count, mesh)
                mesh.name = self.read_uname()
                self.inFile.seek(116, 1)
                self.parse_empty_chunk()
                boneName = self.read_uname()                
                
            elif chunkType == 3:
                self.inFile.seek(56, 1)
                ctype1, xr = self.inFile.read('2H')
                count, count2 = self.inFile.read('2L')
                self.inFile.seek(8, 1)
                self.parse_submesh_chunk(count, mesh)
                mesh.name = self.read_uname()
                self.inFile.seek(96, 1)
                mesh.pos = self.inFile.readBytes(12)
                self.inFile.seek(8, 1)
                self.parse_empty_chunk()
                boneName = self.read_uname()
            elif chunkType == 6:
                self.inFile.seek(48, 1)
                ctype1, xr = self.inFile.read('2H')
                count = self.inFile.readUInt()
                self.inFile.read("%dL" %ctype1)
                self.parse_submesh_chunk(count, mesh)
                mesh.name = self.read_uname()
                self.inFile.seek(112, 1)
                self.parse_empty_chunk()
                self.inFile.readInt()
                mesh.boneName = self.read_uname()
            elif chunkType == 7:
                self.inFile.seek(48, 1)
                ctype1, xr = self.inFile.read('2H')
                count = self.inFile.readUInt()
                self.inFile.read("%dL" %ctype1)
                self.parse_submesh_chunk(count, mesh)
                mesh.name = self.read_uname()
                self.inFile.seek(68, 1)
                self.inFile.readUInt()
                mesh.transform = self.inFile.readBytes(64)
                self.inFile.read('2L')
                self.parse_empty_chunk()
                self.inFile.readInt()
                mesh.boneName = self.read_uname()
            else:
                print(chunkType, self.inFile.tell())
                break
            self.meshList.append(mesh)
        
    def parse_bone_chunks(self, boneCount):
        
        for i in range(boneCount):
            self.inFile.readUInt() # id?
            self.inFile.read('2H')
            unk = self.inFile.readUInt()
            for j in range(unk):
                self.inFile.readUInt()
                self.inFile.read('2H')
                self.inFile.seek(24, 1)
            self.inFile.seek(16, 1)
            boneName = self.read_uname()
            
    def parse_file(self):
        '''Main parser method'''
        
        header = self.parse_header()
        self.inFile.seek(48, 1)
        self.parse_vertices(header.vertChunks)
        self.parse_faces(header.faceChunks)
        self.parse_scripts(header.scriptChunks)
        self.parse_shader_chunks(header.shaderChunks)
        self.parse_material_chunks(header.matChunks)      
        self.parse_texture_chunks(header.texChunks)
        
        print("Scene Root unk", self.inFile.tell())
        self.inFile.readUInt() # root frame has a special integer ?        
        self.parse_frame_chunks(1)
        
        meshCount, frameCount, unk, unk, boneCount = self.inFile.read('5L')
        self.parse_mesh_chunks(meshCount)
        self.parse_frame_chunks(frameCount)
        
        # don't know maybe
        self.parse_bone_chunks(boneCount)
        
        # DONE
        modelName = self.read_uname()
        self.inFile.read('4L')        
        
        print('done', self.inFile.tell())
        print("EOF:", self.inFile.tell() == self.inFile.dataSize)
        self.build_meshes()
    
class Parser2(UCGOParser):
    '''Version 2 parser'''
    
    def parse_material(self):
            
        self.inFile.read('18f')
        self.inFile.read('2H')
        self.inFile.read('2H')
        size = self.inFile.readUInt()
        self.inFile.readUInt()
        self.inFile.readBytes(size)
        self.inFile.readUInt()    
        
    def parse_texture(self):
                
        self.inFile.seek(24, 1)        

class Parser3(UCGOParser):
    '''Version 3 parser'''
    
    def parse_material(self):
        
        self.inFile.read('18f')
        self.inFile.read('2H')
        self.inFile.read('2H')
        size = self.inFile.readUInt()
        self.inFile.readUInt()
        self.inFile.readBytes(size)
        self.inFile.readUInt()
        
    def parse_texture(self):
            
        self.inFile.seek(24, 1)    
    
class Parser4(UCGOParser):
    '''Version 4 parser'''
    
    def parse_material(self):
        
        self.inFile.read('50f')
        self.inFile.read('2H')
        self.inFile.read('2H')
        size = self.inFile.readUInt()
        self.inFile.readUInt()
        self.inFile.readBytes(size)
        self.inFile.readUInt()
        
    def parse_texture(self):
            
        self.inFile.seek(44, 1)    