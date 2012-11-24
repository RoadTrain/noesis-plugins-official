from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    handle = noesis.register("TorchLight",".mesh")
    noesis.setHandlerTypeCheck(handle,noepyCheckType)
    noesis.setHandlerLoadModel(handle,noepyLoadModel)
    return 1

def noepyCheckType(data):
    bs = NoeBitStream(data)
    bs.seek(2,1)
    idstring = noeStrFromBytes(bs.readBytes(22))
    if idstring !='[MeshSerializer_v1.40]': return 0
    return 1

def noepyLoadModel(data, mdlList):
    ctx = rapi.rpgCreateContext()
    mesh = TLMesh(data)
    mesh.Parser()
    mdl=mesh.MakeModel()
    mdlList.append(mdl)
    print(mdlList)
    rapi.rpgClearBufferBinds()
    return 1
    



class TLMesh:
    def __init__(self,data):
        self.data = NoeBitStream(data)
        self.subMesh    = []
        self.vertBuffer = []
        self.vertSize   = []
        self.meshBoneLink    = []
        self.subMeshBoneLink = []
        self.matList = []
        self.boneList = []
    def Mesh(self):
        size = self.data.readUInt()
        self.data.seek(1,1)
    def SubMesh(self):
        size = self.data.readUInt()
        name = b''
        char = self.data.readBytes(1)
        while char != b'\x0a':
            name+=char
            char = self.data.readBytes(1)
        name = noeStrFromBytes(name)
        print(name)
        self.data.seek(1,1)
        print(self.data.tell())
        numIdx = self.data.readUInt()
        self.data.seek(1,1)
        idxBuffer = self.data.readBytes(numIdx*2)
        self.subMesh.append((name,numIdx,idxBuffer))
    def SubMeshOperation(self):
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def SubMeshBoneAssignment(self):
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def SubMeshTextureAlias(self):
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def Geometry(self):
        size = self.data.readUInt()
        self.numVert = self.data.readUInt()
    def GeometryVertexDeclaration(self):
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def GeometryElement(self):
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def VertexBuffer(self):
        size = self.data.readUInt()
        self.data.seek(2,1)
        self.vertSize.append(self.data.readUShort())
        self.data.seek(6,1)
        self.vertBuffer.append(self.data.readBytes(self.vertSize[-1]*self.numVert))
    def VertexBufferData(self): ###Should be empty###
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def MeshSkeletonLink(self):
        size = self.data.readUInt()
        name = b''
        char = self.data.readBytes(1)
        while char != b'\x0a':
            name+=char
            char = self.data.readBytes(1)
        self.skeleton = noeStrFromBytes(name)
    def MeshBoneAssignment(self):
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def MeshLOD(self):
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def MeshLODUsage(self):
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def MeshLODManual(self):
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def MeshLODGenerated(self):
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def MeshBounds(self):
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def SubMeshNameTable(self):
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def SubMeshNameTableElement(self):
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def EdgeList(self):
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def EdgeListLOD(self):
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def EdgeGroup(self):
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def Poses(self):
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def Pose(self):
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def PoseVertex(self):
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def Animations(self):
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def Animation(self):
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def AnimationTrack(self):
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def AnimationMorphKeyFrame(self):
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def AnimationPoseKeyFrame(self):
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def AnimationPoseRef(self):
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def TableExtremes(self):
        size = self.data.readUInt()
        self.data.seek(size-6,1)
    def Parser(self):
        self.data.seek(25,1)
        while self.data.tell() != self.data.dataSize:
            chunk = self.data.readUShort()
            if chunk == 0x3000: self.Mesh()
            elif chunk == 0x4000: self.SubMesh()
            elif chunk == 0x4010: self.SubMeshOperation()
            elif chunk == 0x4100: self.SubMeshBoneAssignment()
            elif chunk == 0x4200: self.SubMeshTextureAlias()
            elif chunk == 0x5000: self.Geometry()
            elif chunk == 0x5100: self.GeometryVertexDeclaration()
            elif chunk == 0x5110: self.GeometryElement()
            elif chunk == 0x5200: self.VertexBuffer()
            elif chunk == 0x5210: self.VertexBufferData()
            elif chunk == 0x6000: self.MeshSkeletonLink()
            elif chunk == 0x7000: self.MeshBoneAssignment()
            elif chunk == 0x8000: self.MeshLOD()
            elif chunk == 0x8100: self.MeshLODUsage()
            elif chunk == 0x8110: self.MeshLODManual()
            elif chunk == 0x8120: self.MeshLODGenerated()
            elif chunk == 0x9000: self.MeshBounds()
            elif chunk == 0xa000: self.SubMeshNameTable()
            elif chunk == 0xa100: self.SubMeshNameTableElement()
            elif chunk == 0xb000: self.EdgeList()
            elif chunk == 0xb100: self.EdgeListLOD()
            elif chunk == 0xb110: self.EdgeGroup()
            elif chunk == 0xc000: self.Poses()
            elif chunk == 0xc100: self.Pose()
            elif chunk == 0xc110: self.PoseVertex()
            elif chunk == 0xc111: self.Animations()
            elif chunk == 0xd000: self.Animation()
            elif chunk == 0xd100: self.AnimationTrack()
            elif chunk == 0xd110: self.AnimationMorphKeyFrame()
            elif chunk == 0xd112: self.AnimationPoseKeyFrame()
            elif chunk == 0xd113: self.AnimationPoseRef()
            elif chunk == 0xe000: self.TableExtremes()
    def GetMaterial(self):
        fName=rapi.getInputName().split('\\')[-1][:-5]
        self.name = fName
        dirPath = rapi.getDirForFilePath(rapi.getInputName())
        self.path = dirPath
        try:
            matFile = open(dirPath+"/"+fName+".material","r")
            while True:
                line = matFile.readline()
                #print(line)
                if "texture " in line: line=line.split(' ')[-1][:-5];print(line);return line
        except:print("[*] Material not found.", );return 0
        print(fName)
    def GetBones(self):
        try:
            boneFile = open(self.path+"/"+self.name+".skeleton","rb").read()
            bs = NoeBitStream(boneFile)
            bs.seek(21,1)
            boneData   = []
            parentData = {}
            i=0
            while bs.tell() != bs.dataSize:
                chunk = bs.readUShort()
                if chunk == 0x2000:
                    bs.seek(4,1)
                    name = b''
                    char = bs.readBytes(1)
                    while char != b'\x0a':
                        name+=char
                        char = bs.readBytes(1)
                    name = noeStrFromBytes(name)
                    bs.seek(2,1)
                    data=bs.read('7f')
                    bone=NoeMat43()
                    bone.__setitem__(3,(data[0],data[2],data[1]))
                    rot = NoeVec3((data[3],data[4],data[5]))
                    rot = rot.toMat43()
                    if i == 53:
                        
                        print(rot.mat43[0])
                        print(rot.mat43[1])
                        print(rot.mat43[2])
                        print(rot.mat43[3])
                    #bone.__setitem__(0,NoeVec3(data[3],0,0))
                    #bone.__setitem__(1,NoeVec3(0,data[4],0))
                    #bone.__setitem__(2,NoeVec3(0,0,data[5]))
                    boneData.append((name,bone))
                    i+=1
                elif chunk == 0x3000:
                    bs.seek(4,1)
                    p = bs.read('2H')
                    parentData[p[0]] = p[1]
                else:
                    size = bs.readUInt()
                    bs.seek(size-6,1)
            for i in range(len(boneData)):
                name = boneData[i][0]
                bone = boneData[i][1]
                if i == len(boneData)-1:parent = -1
                else:parent = parentData[i]
                self.boneList.append(NoeBone(i,name,bone,None,parent))
            self.boneList = rapi.multiplyBones(self.boneList)
        except: print("[*] Skeleton not found.", );raise;return 0
    def MakeModel(self):
        tex = self.GetMaterial()
        bList = self.GetBones()
        print(len(self.subMesh[0][2]),self.subMesh[0][1])
        print(self.vertSize,self.numVert)
        for i in range(len(self.vertBuffer)):
            pass
        rapi.rpgBindPositionBufferOfs(self.vertBuffer[0], noesis.RPGEODATA_FLOAT, self.vertSize[0], 0)
        rapi.rpgBindUV1BufferOfs(self.vertBuffer[1], noesis.RPGEODATA_FLOAT, self.vertSize[1], 0)
        if tex !=0:
            material = NoeMaterial(tex,tex)
            rapi.rpgSetMaterial(tex)
            self.matList.append(material)
        rapi.rpgCommitTriangles(self.subMesh[0][2], noesis.RPGEODATA_USHORT, self.subMesh[0][1], noesis.RPGEO_TRIANGLE, 1)
        #rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, self.numVert, noesis.RPGEO_POINTS, 1)
        mdl = rapi.rpgConstructModel()
        mdl.setBones(self.boneList)
        return mdl
