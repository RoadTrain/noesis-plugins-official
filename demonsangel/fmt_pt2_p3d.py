from inc_noesis import *
import noesis
import rapi

GEO_C = 0
TRI_C = 0
MaterialLink = {}
def registerNoesisTypes():
    handle = noesis.register("Prototype 2",".p3d")
    noesis.setHandlerTypeCheck(handle,noepyCheckType)
    noesis.setHandlerLoadModel(handle,noepyLoadModel)
    return 1

def noepyCheckType(data):


    return 1

def noepyLoadModel(data,mdlList):
    ctx = rapi.rpgCreateContext()
    model = P3D(data)
    
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(model.texList, model.matList))
    mdlList.append(mdl)
    return 1
class P3DBone:
    def __init__(self,data):
        tell = data.tell()
        self.type       = data.readUInt()
        self.size       = data.readUInt()
        self.unk        = data.readUInt()
        self.name       = noeStrFromBytes(data.readBytes(data.readUByte()))
        self.parent     = data.readInt()
        x               = data.read('4f')
        y               = data.read('4f')
        z               = data.read('4f')
        w               = data.read('4f')
        self.mat43      = NoeMat44((x,y,z,w)).toMat43()
        data.seek(tell + self.size)
def P3DIndice(self,data):
    data.seek(4,1)
    name            = noeStrFromBytes(data.readBytes(data.readUByte()))
    self.name       = name
    name            = name.split('_geo_')
    self.modelName  = name[0]
    self.meshName   = name[1].split('_indices')[0]
    data.seek(4,1)
    self.numMesh    = data.readUInt()
    self.numIdx     = data.readUInt()
    data.seek(4,1)
    self.numTri     = data.readUInt()
    #subchunk
    data.seek(4,1)
    data.seek(data.readUInt()-8+16,1)
    self.idxBuffer  = data.readBytes(self.numIdx*2)

def P3DGeo(self,data):
    data.seek(4,1)
    self.name       = noeStrFromBytes(data.readBytes(data.readUByte()))
    data.seek(8,1)
    self.numVert    = data.readUInt()
    data.seek(8+12,1)
    props           = data.readUInt()
    self.props      ={}
    for i in range(props):
        name                = noeStrFromBytes(data.readBytes(data.readUByte()))
        data.seek(8,1)
        self.props[name]    = data.readUInt()
        self.vertLength     = data.readUInt()
        numVert             = data.readUInt()
        if numVert != self.numVert: print("error: numVert doesn't match")
        data.seek(8,1)
    data.seek(12,1)
    length          = data.readUInt()
    self.vertBuffer = data.readBytes(length)
    
    data.seek(12+4,1)
    self.name2      = noeStrFromBytes(data.readBytes(data.readUByte()))
    data.seek(8+4+8+12,1)
    props           = data.readUInt()
    for i in range(props):
        name                = noeStrFromBytes(data.readBytes(data.readUByte()))
        data.seek(8,1)
        self.props[name]    = data.readUInt()
        self.uvLength       = data.readUInt()
        numVert             = data.readUInt()
        if numVert != self.numVert: print("error: numVert doesn't match")
        data.seek(8,1)
    data.seek(12,1)
    length          = data.readUInt()
    self.uvBuffer   = data.readBytes(length)
def P3DMAT(self,data):
    name                = noeStrFromBytes(data.readBytes(data.readUByte()))
    data.seek(4,1)
    data.seek(data.readUByte(),1)
    numSubChunks        = data.readUInt()
    data.seek(4,1)
    data.seek(data.readUInt()-8,1)
    data.seek(4,1)
    data.seek(data.readUInt()-8,1)
    
    material            = NoeMaterial(name, '')
    for i in range(numSubChunks):
        chunk           = data.readUInt()
        size            = data.read('2I')
        if chunk == 69654:
            name        = noeStrFromBytes(data.readBytes(data.readUByte())).lower()
            if name == 'color':
                name    = noeStrFromBytes(data.readBytes(data.readUByte()))
                material.setTexture(name)
            elif name == 'normal':
                name    = noeStrFromBytes(data.readBytes(data.readUByte()))
                material.setNormalTexture(name)
            elif name == 'specular':
                name    = noeStrFromBytes(data.readBytes(data.readUByte()))
                material.setSpecularTexture(name)
            else:
                noeStrFromBytes(data.readBytes(data.readUByte()))
        else:
            data.seek(size[1]-12,1)
    self.material = material

class P3DChunk:
    def __init__(self,data):
        self.type       = data.readUInt()
        self.size       = data.readUInt()
        self.unk        = data.readUInt()
        self.x = 0
        try:
            
            x = getattr(self,"_"+str(self.type))
            x(data)
            self.x=1
            
        except:
            if self.type == 143360 or self.type == 69653 or self.type == 151554:raise
            data.seek(self.size-12,1)
            
        
        
    def _143360(self,data): #armature
        self.name       = noeStrFromBytes(data.readBytes(data.readUByte()))
        self.bones      = []
        data.seek(4,1)
        self.numBones   = data.readUInt()
        data.seek(4,1)
        data.seek(4,1)
        for i in range(self.numBones): 
            self.bones.append(P3DBone(data))
            
    def _69654(self,data): #texture
        data.seek(self.size-12,1)
    def _69667(self,data):
        self.name = noeStrFromBytes(data.readBytes(data.readUByte()))
        #print(self.name)
    def _65601(self,data): #triangle
        P3DIndice(self,data)
    def _65600(self,data):
        P3DGeo(self,data)
    def _69653(self,data):
        P3DMAT(self,data)
    def _151554(self,data):
        data.seek(4,1)
        material        = noeStrFromBytes(data.readBytes(data.readUByte()))
        data.seek(4,1)
        meshName        = noeStrFromBytes(data.readBytes(data.readUByte()))
        noeStrFromBytes(data.readBytes(data.readUByte()))
        noeStrFromBytes(data.readBytes(data.readUByte()))
        data.seek(1,1)
        global MaterialLink
        MaterialLink[meshName] = material
class P3D:
    def __init__(self,data):
        self.data=NoeBitStream(data)
        self.chunks = []
        self.geos   = []
        self.idxs   = []
        self.mats   = []
        while not self.data.checkEOF():
            now = self.data.tell()
            try:y = x
            except:pass
            x = P3DChunk(self.data)
            if x.type == 65601:     self.idxs.append(x)
            elif x.type == 65600:   self.geos.append(x)
            elif x.type == 69653:   self.mats.append(x)
            elif x.x:               self.chunks.append(x)
            after = self.data.tell()
            if after - now <12:
                print("dafuq",now,after,x.type,y.type)
                break
        
        self.CreateGeo()
    def CreateGeo(self):
        print(len(self.idxs))
        x=0
        y=len(self.geos)#8
        n = []#[5,6,7]
        GEO_C = 0
        self.matList    = []
        self.texList    = []
        dirPath         = rapi.getDirForFilePath(rapi.getInputName())
        for mat in self.mats:
            self.matList.append(mat.material)
            mat         = mat.material
            diffuse     = mat.texName
            normal      = mat.nrmTexName
            specular    = mat.specTexName
            for t in [diffuse,normal,specular]:
                try:
                    tex         = open(dirPath + '/' +t,'rb').read()
                    tex         = rapi.loadTexByHandler(tex,'.dds')
                    tex.name    = t
                    self.texList.append(tex)
                except:
                    raise
        
        for i in range(x,x+y):
        #for i in range(len(self.idxs)):
            idx  = self.idxs[i]
            geo  = self.geos[i]
            prop = geo.props
            print("%d: "%i,idx.name," | ",geo.name)
            print(idx.numTri,idx.numIdx,geo.numVert)
            if not i in n:

                #material = self.matList[MaterialLink[idx.name]]
                rapi.rpgSetMaterial(MaterialLink[idx.name])
                rapi.rpgBindPositionBufferOfs   (geo.vertBuffer,   noesis.RPGEODATA_FLOAT,  geo.vertLength, prop['position'])
                rapi.rpgBindUV1BufferOfs        (geo.uvBuffer,     noesis.RPGEODATA_FLOAT,  geo.uvLength,   prop['tex0'])
                rapi.rpgBindNormalBufferOfs     (geo.vertBuffer,   noesis.RPGEODATA_FLOAT,  geo.vertLength, prop['normal'])
                rapi.rpgBindTangentBufferOfs    (geo.vertBuffer,   noesis.RPGEODATA_FLOAT,  geo.vertLength, prop['tangent'])
                rapi.rpgCommitTriangles         (idx.idxBuffer,    noesis.RPGEODATA_USHORT, idx.numIdx,     noesis.RPGEO_TRIANGLE, 1)
                #rapi.rpgCommitTriangles         (idx.idxBuffer,    noesis.RPGEODATA_USHORT, idx.numTri,     noesis.RPGEO_TRIANGLE, 1)
            if GEO_C == 1:
                bs = NoeBitStream()
                fileG = open("geo-%d.p3ddump"%i,'wb')
                bs.writeUInt(geo.numVert)
                bs.writeBytes(geo.vertBuffer)
                bs.writeUInt(idx.numTri)
                bs.writeBytes(idx.idxBuffer)
                fileG.write(bs.getBuffer())
                fileG.close()
