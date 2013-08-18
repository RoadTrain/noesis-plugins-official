from inc_noesis import *
import noesis
import rapi
import os

def registerNoesisTypes():
    handle = noesis.register("Illusion", ".xx")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel) #see also noepyLoadModelRPG
    noesis.setHandlerWriteModel(handle, noepyWriteModel)
    return 1

#check if it's this type based on the data
def noepyCheckType(data):

    return 1

#load the model
def noepyLoadModel(data, mdlList):
    ctx = rapi.rpgCreateContext()
    parser = Illusion_XX(data)
    parser.parse_file()
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
    mdl.setBones(parser.boneList)
    mdlList.append(mdl)
    return 1

def noepyWriteModel(mdl, bs):
    
    if mdl:
        writer = XX_Export(mdl, bs)
        writer.write_file()
        return 1
    return 0

def get_directory_path():
    
    dirPath = rapi.getDirForFilePath(rapi.getInputName())
    if not dirPath:
        dirPath = os.path.dirname(os.path.abspath(rapi.getInputName())) + os.sep
    return dirPath

class XX_Texture(object):
    
    def __init__(self):
        
        self.name = ""
        self.path = ""
        self.size = 0
        self.width = 0
        self.height = 0
        self.ext = ""
        self.data = bytes()
        
class XX_Material(object):
    
    def __init__(self):
        
        self.name = ""
        self.texName = ""
        self.specName = ""
        self.normName = ""
        self.alphaName = ""

class XX_Frame(object):
    '''An Illusion XX Frame object'''
    
    def __init__(self, index):
        self.index = index
        self.parent = -1
        self.name = ""
        self.children = []
        self.meshes = []
        self.transform = NoeMat44()
    
class XX_Model(object):
    '''The XX object'''
    
    def __init__(self):
        
        self.frames = []
        self.materials = []
        self.textures = []
        
    def add_frame_child(self, index, frame):
        
        self.frames[index].children.append(frame)
        
    def add_frame_mesh(self, index, mesh):
        
        self.frames[index].meshes.append(mesh)
    
class XX_Export(object):
    
    def __init__(self, model, outFile):    
        
        self.xxFormat = -1
        self.outFile = outFile
        self.mdl = model
        self.dirpath = get_directory_path()
        
        self.xxFile = XX_Model()

        #helper attributes
        self.matList = []
        self.texList = []
        self.texNames = []
        self.matNames = [] #for index lookups
        
    def encrypt_string(self, string):
        '''Return the encrypted string. XOR each character in the string by
        FF to get the actual character. Strings are null-terminated.'''
        
        outStr = bytes()
        for i in range(len(string)):
            outStr += struct.pack("B", ord(string[i]) ^ 0xFF)
        return outStr
    
    def write_name(self, name):
        '''All names are null-terminated, preceded with the length of the
        string, including the null-char'''
        
        if name:
            string = self.encrypt_string(name + "\x00")
            self.outFile.writeUInt(len(string))
            self.outFile.writeBytes(string)
        else:
            self.outFile.writeUInt(0)
    
    def write_material_textures(self, mat):
        
        #diffuse map
        diffuseTex = os.path.basename(mat.texName)
        self.write_name(diffuseTex)
        self.outFile.writeBytes(b'\x00' * 16)
        
        #specular map?
        self.write_name("")
        self.outFile.writeBytes(b'\x00' * 16)
        
        #normal map?
        self.write_name("")
        self.outFile.writeBytes(b'\x00' * 16)        
                
        #alpha map?
        self.write_name("")
        self.outFile.writeBytes(b'\x00' * 16)        
        
    def write_materials(self):
        
        #self.outFile.writeBytes(b"\x9A\x19\x07\x44")
        self.outFile.writeBytes(b"\x00\x00\xE0\x40")
        numMat = len(self.matList)
        self.outFile.writeUInt(numMat)
        for i in range(numMat):
            
            mat = self.matList[i]
            ambient = NoeVec4((-1, -1, -1, -1))
            diffuse = NoeVec4((-1, -1, -1, -1))
            emissive = NoeVec4((-0.2, -0.2, -0.2, -1))
            specular = NoeVec4((0, 0, 0, -1))
            power = -20
            matUnk1 = b"\x00\x01\x02\x03"
            
            self.write_name(mat.name)
            self.outFile.writeBytes(ambient.toBytes())
            self.outFile.writeBytes(diffuse.toBytes())
            self.outFile.writeBytes(specular.toBytes())
            self.outFile.writeBytes(emissive.toBytes())
            self.outFile.writeFloat(power)
            self.write_material_textures(mat)
            self.outFile.writeBytes(matUnk1)
            self.outFile.writeBytes(b'\x00' * 84)
	        
    def write_textures(self):
        
        #how many textures we actually find
        texFound = 0
        numTex = len(self.texList)
        pos = self.outFile.tell()
        self.outFile.writeUInt(numTex)
        for tex in self.texList:
            texName = tex.name
            unk1 = b'\x00\x00\x00\x00'
            unk2 = b'\x01\x00\x00\x00\x01\x00\x00\x00\x14\x00\x00\x00\x03\x00\x00\x00\x03\x00\x00\x00'
            texture = rapi.loadTexByHandler(tex.data, tex.ext)
            if texture:
                self.write_name(texName)
                self.outFile.writeBytes(unk1)
                self.outFile.writeUInt(texture.width)
                self.outFile.writeUInt(texture.height)
                self.outFile.writeBytes(unk2)
                self.outFile.writeByte(1) #checksum
                self.outFile.writeUInt(tex.size)
                self.outFile.writeBytes(tex.data)
                texFound += 1
            else:
                print("%s not found" %texName)
                continue
            
        curr = self.outFile.tell()
        self.outFile.seek(pos)
        self.outFile.writeUInt(texFound)
        self.outFile.seek(curr)
            
    def write_dupe_vertices(self, mesh):
        
        self.outFile.writeUShort(0) #no dupes
        self.outFile.writeBytes(b"\x12\x01\x00\x00\x20\x00\x00\x00")
        
    def write_vertices(self, mesh, numVerts):
        
        for i in range(numVerts):
            
            if self.xxFormat >= 4:
                self.outFile.writeUShort(i)
            else:
                self.outFile.writeUInt(i)            
            self.outFile.writeBytes(mesh.positions[i].toBytes())
            self.outFile.writeBytes(NoeVec3().toBytes())
            self.outFile.writeBytes(b"\x00\x00\x00\x00")
            self.outFile.writeBytes(mesh.normals[i].toBytes())
            self.outFile.writeBytes(mesh.uvs[i].toBytes()[:8])
            
    def write_faces(self, mesh, numIdx):
        
        for i in range(numIdx):
            self.outFile.writeUShort(mesh.indices[i])
            
    def write_mesh_unknowns(self, numVerts, meshType):
        
        #unknown A
        self.outFile.writeBytes(b'\x00' * (numVerts * 8 * meshType))
        
        #unknown B
        self.outFile.writeBytes(b'\x00' * 100)
        
        #unknown C
        if self.xxFormat >= 3:
            self.outFile.writeBytes(b'\x00' * 64)
            
        #unknown D
        if self.xxFormat >= 5:
            self.outFile.writeBytes(b'\x00' * 20)
            
        #unknown E
        if self.xxFormat >= 6:
            self.outFile.writeBytes(b'\x00' * 28)
        
    def write_mesh(self, mesh, meshType):

        meshName = mesh.name
        meshMat = mesh.matName
        numVerts = len(mesh.positions)
        numIdx = len(mesh.indices)
        meshUnk = b'\x02\x64\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        try:
            matNum = self.matNames.index(meshMat)        
        except:
            matNum = -1
        
        self.outFile.writeBytes(meshUnk)
        self.outFile.writeUInt(matNum)
        self.outFile.writeUInt(numIdx)
        self.write_faces(mesh, numIdx)
        self.outFile.writeUInt(numVerts)
        self.write_vertices(mesh, numVerts)        
        self.write_mesh_unknowns(numVerts, meshType)
        
    def write_bones(self, mesh):
        
        #hardcode
        self.outFile.writeUInt(0)
    
    def write_frame(self, root):
        
        index = root.index
        name = root.name
        subframes = root.children
        meshes = root.meshes
        transform = root.transform
        numChildren = len(subframes)
        numMesh = len(meshes)
        unkA = struct.pack("4L", *[0, 100, 0, 0]) #harcode
        
        if numMesh:
            unkB = b"\x00\x02\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00"
        else:
            unkB = b"\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        bbMin = self.xxFile.bbox_min
        bbMax = self.xxFile.bbox_max
        
        self.write_name(name)
        self.outFile.writeUInt(numChildren)
        self.outFile.writeBytes(transform.toBytes())
        self.outFile.writeBytes(unkA)
        self.outFile.writeUInt(numMesh)
        self.outFile.writeBytes(bbMin.toBytes())
        self.outFile.writeBytes(bbMax.toBytes())
        self.outFile.writeBytes(unkB)
        
        if numMesh > 0:
            meshType = 0
            self.outFile.writeUByte(meshType)
            for i in range(numMesh):
                mesh = meshes[i]
                self.write_mesh(mesh, meshType)
            self.write_dupe_vertices(mesh)
            self.write_bones(mesh)
            
        for i in range(numChildren):
            self.write_frame(subframes[i])
        
    #A couple helper functions
    
    def write_header(self):
        
        self.outFile.writeUInt(self.xxFormat)
        self.outFile.writeUByte(0)
        self.outFile.writeFloat(6.05)
        self.outFile.writeFloat(0)
        self.outFile.writeBytes(b"\x00" * 13)
        
    def load_texture(self, texPath, ext):
        
        imageData = bytes()
        if os.path.exists(texPath):
            f = open(texPath, 'rb')
            data = f.read()
            f.close()
            
            if ext.lower() == ".bmp":
                imageData = bytes()
                imageData += b'\x00\x00'
                imageData += data[2:]
            else:
                imageData = data
        return imageData
        
    def check_texture(self, texName):
        
        
        filename, ext = os.path.splitext(texName)
        if ext != ".png":
            texName = filename + ext + ".png"
            ext = ".png"
        path = os.path.abspath(texName)
        if texName not in self.texNames:
            imageData = self.load_texture(path, ext)
            tex = XX_Texture()
            tex.name = texName
            tex.path = path
            tex.size = len(imageData)
            tex.data = imageData
            tex.ext = ext
            
            self.texNames.append(texName)
            if tex.size > 0:
                self.texList.append(tex)
        return texName
            
    def check_materials(self):
        
        if self.mdl.modelMats:
            for mat in self.mdl.modelMats.matList:
                material = XX_Material()
                material.name = mat.name
                texName = self.check_texture(mat.texName)
                material.texName = texName
                
                self.matNames.append(mat.name)
                self.matList.append(material)
        
    def calculate_bounding_box(self):
        
        minx, miny, minz = 999999999, 9999999, 99999999
        maxx, maxy, maxz = 0, 0, 0
        
        for mesh in self.mdl.meshes:
            for x, y, z in mesh.positions:
                minx = min(minx, x)
                miny = min(miny, y)
                minz = min(minz, z)
                maxx = max(maxx, x)
                maxy = max(maxy, y)
                maxz = max(maxz, z)
                
        self.xxFile.bbox_min = NoeVec3((minx, miny, minz))
        self.xxFile.bbox_max = NoeVec3((maxx, maxy, maxz))

    def build_frame(self, name, index, parent):
        
        frame = XX_Frame(index)
        frame.name = name
        if parent != -1:
            self.xxFile.add_frame_child(parent, frame)
            frame.parent = parent
            frame.transform = NoeMat44()
        self.xxFile.frames.append(frame)
        
    def check_frames(self):
        
        self.build_frame("All_Root", 0, -1)
        self.build_frame("SCENE_ROOT", 1, 0)
        
        meshes = self.mdl.meshes
        index = 2
        for i in range(len(meshes)):
            mesh = meshes[i]
            self.build_frame(mesh.name, index, 1)
            self.xxFile.add_frame_mesh(index, mesh)
            index += 1
	
    def write_file(self):
        
        #hardcode format and initialize an XX file
        self.xxFormat = 3
        self.check_frames()
        self.check_materials()
        self.calculate_bounding_box()
        self.write_header()

        #write frames
        root = self.xxFile.frames[0]
        self.write_frame(root)
        self.write_materials()
        self.write_textures()
        if self.xxFormat >= 2:
            self.outFile.writeBytes(b"\x00" * 10)

class Illusion_XX(object):
    
    def __init__(self, data):    
        
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.meshInfo = []
      
    def decrypt_string(self, string):
        '''Return the decrypted string. XOR each character in the string by
        FF to get the actual character. Strings are null-terminated.'''
        
        inverted = ""
        for i in range(len(string)-1):
            inverted += chr(string[i] ^ 0xFF)
        return inverted
    
    def read_name(self):
        
        length = self.inFile.readUInt()
        return self.decrypt_string(self.inFile.readBytes(length))
    
    def get_format(self):
        
        xxFormat = 0
        fmt = self.inFile.readUByte()
        xxInt = self.inFile.read('4B')
        if (fmt >= 0x01 and fmt <= 0x06 and xxInt[0] == 0):
            xxFormat = fmt
        elif xxInt[2] == 0x3F:
            xxFormat = -1
        return xxFormat
    
    def build_meshes(self):
            
        for meshInfo in self.meshInfo:
            
            vertBuff = meshInfo[0]
            idxBuff = meshInfo[1]
            numIdx = meshInfo[2]
            matNum = meshInfo[3]
            meshName = meshInfo[4]
            
            if self.xxFormat >= 4:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 70, 2)
                rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 70, 30)
                rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 70, 42)
            else:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 52, 4)
                rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 52, 32)
                rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 52, 44)
            
            if len(self.matList) > matNum:
                mat = self.matList[matNum]            
                matName = mat.name
                rapi.rpgSetMaterial(matName)
            rapi.rpgSetName(meshName)
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
            rapi.rpgClearBufferBinds()    
    
    def parse_textures(self, numTex):
        
        for i in range(numTex):
            texName = self.read_name()
            texUnk1 = self.inFile.readBytes(4)
            width, height = self.inFile.read('2L')
            
            texUnk2 = self.inFile.readBytes(20)
            checksum = self.inFile.readByte()
            dataSize = self.inFile.readUInt()
            ext = os.path.splitext(texName)[1]
            data = self.inFile.readBytes(dataSize)
            if ext == ".bmp":
                texData = bytes()
                texData += b'\x42\x4D'
                texData += data[2:]
                tex = rapi.loadTexByHandler(texData, ext)
            else:
                tex = rapi.loadTexByHandler(data, ext)
           
            if tex is not None:
                tex.name = texName
                self.texList.append(tex)   

                
    def parse_materials(self, numMat):

        for i in range(numMat):
            matName = self.read_name()
            diffuse = self.inFile.read('4f')
            ambient = self.inFile.read('4f')
            specular = self.inFile.read('4f')
            emissive = self.inFile.read('4f')
            power = self.inFile.readFloat()
            
            diffuseName = self.read_name()
            diffuseUnknown = self.inFile.readBytes(16)
            
            specName = self.read_name()
            self.inFile.readBytes(16)
           
            normName = self.read_name()
            self.inFile.readBytes(16)
            
            alphaMap = self.read_name()
            self.inFile.readBytes(16)            
            if self.xxFormat < 0:
                matUnk1 = self.inFile.readBytes(4)
            else:
                matUnk1 = self.inFile.readBytes(88)
                
            material = NoeMaterial(matName, "")
            material.setTexture(diffuseName)
            self.matList.append(material)
    
    def parse_faces(self, numIdx):

        idxList = self.inFile.readBytes(numIdx * 2)
        return idxList
        
    def parse_vertices(self, numVerts):

        if self.xxFormat >= 4:
            vertBuff = self.inFile.readBytes(numVerts*70)
        else:
            vertBuff = self.inFile.readBytes(numVerts*52) 
        return vertBuff
    
    def parse_dupe_vertices(self, numVertDupe):
        
        for i in range(numVertDupe):
            if self.xxFormat >= 4:
                index = self.inFile.readUShort()
            else:
                index = self.inFile.readUInt()
            
            self.inFile.readBytes(48)
            #vx, vy, vz = self.inFile.read('3f')
            #weights = self.inFile.read('3f')
            #boneIndices = self.inFile.read('4B')
            #nx, ny, nz = self.inFile.read('3f')
            #tu, tv = self.inFile.read('2f')
            
            if self.xxFormat >= 4:
                unk = self.inFile.readBytes(20)
            else:
                unk = 0
        
    def parse_bones(self, numBones):
        
        #DOES NOT WORK
        prev = ""
        for i in range(numBones):
            boneName = self.read_name()
            boneIndex = self.inFile.readUInt()
            boneMat = NoeMat44.fromBytes(self.inFile.readBytes(64)).toMat43()
            bone = NoeBone(boneIndex, boneName, boneMat, prev, i-1)
            self.boneList.append(bone)
            prev = boneName
    
    def parse_mesh(self, numMesh, name):
    
        if self.xxFormat > 6:
            meshName = self.read_name()
        else:
            meshName = name
        meshType = self.inFile.readByte()
        for i in range(numMesh):
            if numMesh == 1:
                objName = meshName
            else:
                objName = "%s[%d]" %(meshName, i)
    
            meshUnknown = self.inFile.read('4f')   #unknown
            matNum = self.inFile.readUInt()  #material index
            numIdx = self.inFile.readUInt()
            idxBuff = self.parse_faces(numIdx)
            
            numVerts = self.inFile.readUInt()
            vertBuff = self.parse_vertices(numVerts)
            
            unknownA = self.inFile.readBytes(numVerts * 8 * meshType)
            if self.xxFormat >= 2:
                unknownB = self.inFile.readBytes(100)
            if self.xxFormat >= 3:
                unknownC = self.inFile.readBytes(64)        
            if self.xxFormat >= 5:
                unknownD = self.inFile.readBytes(20)   
            if self.xxFormat >= 6:
                unknownE = self.inFile.readBytes(28)
            
            self.meshInfo.append([vertBuff, idxBuff, numIdx, matNum, objName])
        
        numVertDupe = self.inFile.readUShort()
        self.inFile.read('2L')
        self.parse_dupe_vertices(numVertDupe)     
        numBones = self.inFile.readUInt()
        self.parse_bones(numBones)
            
    def parse_frames(self):
        
        frameName = self.read_name()
        numChildren = self.inFile.readUInt()  #numChildFrames
        frameTransform = self.inFile.read('16f')    #transform matrix
        frameUnknownA = self.inFile.read('4f')      #unknown
        
        numMesh = self.inFile.readUInt()
        bbMin = self.inFile.read('3f')   #min bounds
        bbMax =  self.inFile.read('3f')   #max bounds
        frameUnknownB = self.inFile.read('4f')   #unknown
        if self.xxFormat == 6:
            unk5 = self.inFile.readUInt()

        if numMesh > 0:
            self.parse_mesh(numMesh, frameName)
        for j in range(numChildren):
            childFrames = self.parse_frames()
            
        #frame.name = frameName
        #frame.numChildren = numChildren
        #frame.transform = frameTransform
        #frame.unknownA = frameUnknownA
        #frame.numMesh = numMesh
        #frame.bbMin = bbMin
        #frame.bbMax = bbMax
        #frame.unknownB = frameUnknownB
        #frame.childFrames = childFrames
                    
    def parse_file(self):
        
        self.xxFormat = self.get_format()
        self.inFile.seek(0)
        
        #objectSection [0] unknown
        if self.xxFormat > 0:
            self.inFile.seek(26, 1)
        else:
            self.inFile.seek(21, 1)
        self.parse_frames()
        matSectUnknown = self.inFile.readBytes(4)
        numMat = self.inFile.readUInt()
        self.parse_materials(numMat)
        numTex = self.inFile.readUInt()
        self.parse_textures(numTex)
        
        ##unknown object end
        #if self.xxFormat < 2:
            #unk = 0
        #else:
            #unk = self.inFile.seek(10, 1)
            
        self.build_meshes()