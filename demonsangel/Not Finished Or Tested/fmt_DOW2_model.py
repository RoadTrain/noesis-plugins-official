'''
Created on 24-nov.-2012

@author: Andrew
'''
####################################################################
#################             IMPORTANT            #################
####################################################################
"""
Change the following variable 'ARTPATH' to either your completely extracted art folder if you have extracted the entire sga
If your art folder is at 'c:\Games\Dawn of War\Assets\Art' then change ARTPATH to ARTHPATH =  r'c:\Games\Dawn of War\Assets'
If you want to put all the textures in the model folder yourself change ARTPATH to ARTPATH = None
    If you use this option the script will let you know which textures are missing.
"""
ARTPATH = r'D:\Games\Warhammer\GameAssets\Archives\DATA'

### DO NO CHANGE BELOW HERE
from inc_noesis import *
import noesis
import rapi
import os

def registerNoesisTypes():
    handle = noesis.register("Dawn of War 2", ".model")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1
    
def noepyCheckType(data):
    data    = NoeBitStream(data)
    magic   = noeStrFromBytes(data.readBytes(12))
    noesis.logPopup()
    if magic.lower() != 'relic chunky':
        return 0
    return 1

def noepyLoadModel(data, mdlList):
    
    ctx = rapi.rpgCreateContext()
    
    file = MODEL(data)
    mdlList.append(file.mdl)
    rapi.rpgClearBufferBinds()
    return 1

def LoadTexture(texName):
    if ARTPATH == None:
        name = rapi.getDirForFilePath(rapi.getInputName())+texName
    else:
        name = texName.split('\\')[-1]
    tex = open(name,'rb').read()
    tex = rapi.loadTexByHandler(tex,'.dds')
    tex.name = texName
    return tex
class FOLDMODL:
    def __init__(self, parent):
        data            = parent.data
        self.version    = data.readUInt()
        self.length     = data.readUInt()
        data.seek(8,1)
        parent.modelName = noeStrFromBytes(data.readBytes(self.length))
        return
    
class FOLDMTRL:
    def __init__(self,parent):
        data = self.data = parent.data
        self.version    = data.readUInt()
        self.length     = data.readUInt()
        data.seek(8,1)
        self.matName    = noeStrFromBytes(data.readBytes(self.length))
        
        self.DATAINFO()
        
        self.texList = []
        
        for i in range(21):
            self.DATAVAR()
        
        self.CREATE(parent)
        return
    
    def DATAINFO(self):
        self.data.seek(16,1)
        length = self.data.readUInt()
        self.data.seek(8,1)
        noeStrFromBytes( self.data.readBytes( length))
        self.type = noeStrFromBytes( self.data.readBytes( self.data.readUInt()))
        return
    
    def DATAVAR(self):
        self.data.seek(16,1)
        length = self.data.readUInt()
        self.data.seek(8,1)
        noeStrFromBytes( self.data.readBytes( length))
        type = noeStrFromBytes( self.data.readBytes( self.data.readUInt()))
        self.data.seek(4,1)
        if type == 'teamTex':
            texName = noeStrFromBytes( self.data.readBytes( self.data.readUInt()))
            self.texList.append( LoadTexture(texName))
            self.texTeam = self.texList[-1]
        elif type == 'dirtTex':
            texName = noeStrFromBytes( self.data.readBytes( self.data.readUInt()))
            self.texList.append( LoadTexture(texName))
            self.texDirt = self.texList[-1]
        elif type == 'bHighlight':
            self.data.seek(4,1)
            if self.data.readUInt() == 1: self.highlight = True
            else: self.highlight = False
        elif type == 'badge2Tex':
            texName = noeStrFromBytes( self.data.readBytes( self.data.readUInt()))
            self.texList.append( LoadTexture(texName))
            self.texBadge2 = self.texList[-1]
        elif type == 'badge1Tex':
            texName = noeStrFromBytes( self.data.readBytes( self.data.readUInt()))
            self.texList.append( LoadTexture(texName))
            self.texBadge1 = self.texList[-1]
        elif type == 'badge2MatrixRow1Row2':
            self.data.seek(4,1)
            self.badge2 = self.data.read('4f')
        elif type == 'emissiveMultiplier':
            self.data.seek(4,1)
            self.emi = self.data.readFloat()
        elif type == 'normalMap':
            texName = noeStrFromBytes( self.data.readBytes( self.data.readUInt()))
            self.texList.append( LoadTexture(texName))
            self.texNormal = self.texList[-1]
        elif type == 'unitOcclusionFlag':
            self.data.seek(4,1)
            self.occlusion = self.data.readUInt()
        elif type == 'diffuseTex':
            texName = noeStrFromBytes( self.data.readBytes( self.data.readUInt()))
            self.texList.append( LoadTexture(texName))
            self.texDiffuse = self.texList[-1]
        elif type == 'emissiveTex':
            texName = noeStrFromBytes( self.data.readBytes( self.data.readUInt()))
            self.texList.append( LoadTexture(texName))
            self.texEmissive = self.texList[-1]
        elif type == 'badge1MatrixRow1Row2':
            self.data.seek(4,1)
            self.badge1 = self.data.read('4f')
        elif type == 'specularTex':
            texName = noeStrFromBytes( self.data.readBytes( self.data.readUInt()))
            self.texList.append( LoadTexture(texName))
            self.texSpecular = self.texList[-1]
        elif type == 'World':
            self.data.seek(4,1)
            self.world = self.data.read('16f')
        elif type == 'dirtVisibility':
            self.data.seek(4,1)
            self.dirt = self.data.readFloat()
        elif type == 'uOffset':
            self.data.seek(4,1)
            self.uOffset = self.data.readFloat()
        elif type == 'badge2Translate':
            self.data.seek(4,1)
            self.badge2Translate = self.data.read('4f')
        elif type == 'glossTex':
            texName = noeStrFromBytes( self.data.readBytes( self.data.readUInt()))
            self.texList.append( LoadTexture(texName))
            self.texGloss = self.texList[-1]
        elif type == 'vOffset':
            self.data.seek(4,1)
            self.vOffset = self.data.readFloat()
        elif type == 'badge1Translate':
            self.data.seek(4,1)
            self.badge1Translate = self.data.read('4f')
        elif type == 'occlusionTex':
            texName = noeStrFromBytes( self.data.readBytes( self.data.readUInt()))
            self.texList.append( LoadTexture(texName))
            self.texOcclusion = self.texList[-1]
        else: raise
        return
    
    def CREATE(self, parent):
        mat = NoeMaterial(self.matName,'')
        mat.setTexture(self.texDiffuse)
        mat.setNormalTexture(self.texNormal)
        mat.setSpecularTexture(self.texSpecular)
        parent.matList.append(mat)
        for tex in self.texList:
            parent.texList.append(tex)
    
class FOLDMESH:
    def __init__(self,parent):
        return
    
class DATAMRKS:
    def __init__(self,parent):
        return
    
CHUNK   = {1279545165: FOLDMODL,
           1280463949: FOLDMTRL,
           1213416781: FOLDMESH,
           1397445197: DATAMRKS}

class MODEL:
    def __init__(self,data):
        self.data = NoeBitStream(data)
        self.boneList       = []
        self.matList        = []
        self.texList        = []
        self.triList        = []
        self.animList       = []
        self.drawCallFace   = []
        self.numDrawCall    = []
        self.matID          = []
        self.vertBuff       = []
        self.idxBuff        = []
        self.numVert        = []
        self.numTri         = []
        self.boneId         = []
        
        self.parse()
        return
    
    def parse(self):
        self.data.seek(36)
        while not self.data.checkEOF():
            chunk = self.data.readUInt()
            ID  = self.data.readUInt()
            try:
                CHUNK[ID](self)
            except:
                break
        