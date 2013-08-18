from inc_noesis import *
import noesis
import rapi
import os

#Define token constants

TOKEN_NAME = 1
TOKEN_STRING = 2
TOKEN_INTEGER = 3
TOKEN_GUID = 5
TOKEN_INTEGER_LIST = 6
TOKEN_FLOAT_LIST = 7
TOKEN_OBRACE = 10
TOKEN_CBRACE = 11
TOKEN_OPAREN = 12
TOKEN_CPAREN = 13
TOKEN_OBRACKET = 14
TOKEN_CBRACKET = 15
TOKEN_OANGLE = 16
TOKEN_CANGLE = 17
TOKEN_DOT = 18
TOKEN_COMMA = 19
TOKEN_SEMICOLON = 20
TOKEN_TEMPLATE = 31
TOKEN_WORD = 40
TOKEN_DWORD = 41
TOKEN_FLOAT = 42
TOKEN_DOUBLE = 43
TOKEN_CHAR = 44
TOKEN_UCHAR = 45
TOKEN_SWORD = 46
TOKEN_SDWORD = 47
TOKEN_VOID = 48
TOKEN_LPSTR = 49
TOKEN_UNICODE = 50
TOKEN_CSTRING = 51
TOKEN_ARRAY = 52

RECORD_BEARING = [TOKEN_NAME, TOKEN_STRING, TOKEN_INTEGER, TOKEN_GUID, 
                  TOKEN_INTEGER_LIST, TOKEN_FLOAT_LIST]

def registerNoesisTypes():
    '''Register the plugin'''
    
    handle = noesis.register("DirectX Binary", ".x;.sxm")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel) #see also noepyLoadModelRPG
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin.'''
    
    if len(data) < 16:
        return 0
    bs = NoeBitStream(data)
    header = noeStrFromBytes(bs.readBytes(4))
    if header != "xof ":
        return 0
    version = bs.read('2H')
    format = noeStrFromBytes(bs.readBytes(4))
    if format != "bin ":
        return 0
    return 1
 
def noepyLoadModel(data, mdlList):
    '''Load the model'''
    
    ctx = rapi.rpgCreateContext()
    parser = DirectX_XBIN(data)
    parser.parse_file()
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
    #mdl.setBones(parser.boneList)
    mdlList.append(mdl)
    return 1

class Template(object):
    '''A template class that may contain tokens and other templates'''
    
    def __init__(self, parent):
        
        self.parent = parent
        self.templates = []
        self.tokens = []
        self.name = ""
        self.isDefinition = False
        
    def __repr__(self):
        
        return "Template: %s" %self.name
    
    def get_token(self):
        
        if self.tokens:
            return self.tokens.pop(0)
        else:
            return None
        
    def add_name(self, name):
        
        if not self.name:
            self.name = name
        
    def add_token(self, token):
        
        self.tokens.append(token)
        
    def add_template(self, template):
        
        self.templates.append(template)
        
    def template_count(self):
        
        count = 0
        if self.templates:
            for template in self.templates:
                count = template.template_count()
        return len(self.templates) + count
    
    def print_templates(self, depth = 0):
        '''Recursively prints out contents of the template and any nested
        templates'''
        
        print("   "*depth, "|-", self.name, self.tokens)
        for template in self.templates:
            template.print_templates(depth+1)

class Token(object):
    '''A generic token'''
    
    def __init__(self, tokenID):
        
        self.token = tokenID
        
    def __repr__(self):
        
        return "<<%s>>" %self.token
    
    def __eq__(self, other):
        
        return self.token == other

class RecordToken(Token):
    '''A record bearing token. Contains values'''
    
    def __init__(self, tokenID):
        
        super(RecordToken, self).__init__(tokenID)
        self.value = ""
        
    def get_value(self):
        
        return self.value
    
    def __repr__(self):
        
        if self.token == TOKEN_NAME:
            return "<<%s>>" %self.value
        else:
            return "<<%s>>" %self.token
    
class DirectX_XBIN(object):
    
    def __init__(self, data):    
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.meshes = []
        self.materials = []
        self.dirpath = rapi.getDirForFilePath(rapi.getInputName())

    def read_name(self):
        
        string = self.inFile.readBytes(self.inFile.readUInt())
        return noeStrFromBytes(string)
        
    def parse_header(self):
        
        header = self.inFile.readBytes(16)
        
    def parse_token_guid(self):
        
        return self.inFile.read('16B')
    
    def parse_int_list(self):
        
        numInt = self.inFile.readUInt()
        return [numInt, self.inFile.readBytes(4*numInt)]

    def parse_float_list(self):
        
        numFloat = self.inFile.readUInt()
        data = self.inFile.readBytes(4*numFloat)
        return [numFloat, data]
    
    def update_template(self, tokens, template):
        
        for token in tokens:
            if token == TOKEN_TEMPLATE:
                template.isDefinition = True
            elif token == TOKEN_NAME:
                if not template.name:
                    template.add_name(token.value)
                else:
                    template.add_token(token)
    
    def read_token(self, parent, tokens=None):
        '''Read tokens for the template. Additional tokens may have been parsed
        for this template before the OBRACE and are available in tokens'''
        
        template = Template(parent)
        if tokens:
            self.update_template(tokens, template)

        #temp token storage, for things like template name which is defined
        #before the open brace 
        temp = []
        
        #parse token  
        while self.inFile.tell() != self.inFile.dataSize:
            
            token = self.inFile.readUShort()
            if token in RECORD_BEARING:
                new_token = RecordToken(token)
                if token == TOKEN_NAME:
                    name = self.read_name()
                    new_token.value = name
                    temp.append(new_token)
                elif token == TOKEN_STRING:
                    name = self.read_name()
                    terminator = self.inFile.readUShort()
                    new_token.value = name
                    template.add_token(new_token)
                elif token == TOKEN_INTEGER:
                    value = self.inFile.readUInt()
                    new_token.value = value
                    template.add_token(new_token)
                elif token == TOKEN_GUID:
                    self.parse_token_guid()
                    template.add_token(new_token)
                elif token == TOKEN_INTEGER_LIST:
                    value = self.parse_int_list()
                    new_token.value = value
                    template.add_token(new_token)
                elif token == TOKEN_FLOAT_LIST:
                    value = self.parse_float_list()
                    new_token.value = value
                    template.add_token(new_token)
            elif token == TOKEN_TEMPLATE:
                new_token = Token(token)
                temp.append(new_token)
            elif token == TOKEN_OBRACE:
                #nested template
                new_template = self.read_token(template, temp)
                temp = []
            elif token == TOKEN_CBRACE:
                parent.add_template(template)
                return template
            elif token == TOKEN_OPAREN:
                pass
            elif token == TOKEN_CPAREN:
                pass
            elif token == TOKEN_DOT:
                pass
            elif token == TOKEN_OBRACKET:
                pass
            elif token == TOKEN_CBRACKET:
                pass
            elif token == TOKEN_ARRAY:
                pass
            elif token == TOKEN_SEMICOLON:
                pass
            elif token == TOKEN_FLOAT:
                pass
            elif token == TOKEN_DWORD:
                pass
            elif token == TOKEN_LPSTR:
                pass
            else:
                print("unknown token", token, self.inFile.tell())
                break
            
        #add everything to the root
        parent.add_template(template)
        return template
            
    def parse_file(self):
        
        self.parse_header()
        root = Template(None)
        binx = self.read_token(root)
        binx.add_name("root")
        
        #binx.print_templates()
        #Build the model
        self.traverse_templates(binx, None)
        self.build_model()
        
    #====================================================
    
    def build_faces(self, idxBuff, matUsed, materials):
        
        start = 0
        for i in range(len(matUsed)):
            numIdx = matUsed[i] * 3
            end = start + numIdx * 4
            buff = idxBuff[start:end]
            rapi.rpgSetMaterial(materials[i])
            rapi.rpgCommitTriangles(buff, noesis.RPGEODATA_UINT, numIdx, noesis.RPGEO_TRIANGLE, 1)
            
            start = end
    
    def build_model(self):
        
        for mesh in self.meshes:
            
            positions = mesh["pos"]
            rapi.rpgBindPositionBuffer(positions, noesis.RPGEODATA_FLOAT, 12)
            
            if "norms" in mesh:
                normals = mesh["norms"]
                #rapi.rpgBindNormalBuffer(normals, noesis.RPGEODATA_FLOAT, 12)
            if "uv" in mesh:
                uv = mesh["uv"]
                rapi.rpgBindUV1Buffer(uv, noesis.RPGEODATA_FLOAT, 8)
                
            if "matIndexes" in mesh:
                matUsed = mesh["matIndexes"]
                
            idxBuff = mesh["idx"]
            numIdx = mesh["numIdx"]
            #print(numIdx)
            if "materials" in mesh:
                materials = mesh["materials"]
            else:
                materials = self.materials
            #rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_UINT, numIdx, noesis.RPGEO_TRIANGLE, 1)
            self.build_faces(idxBuff, matUsed, materials)
            rapi.rpgClearBufferBinds()
        
    #====================================================
        
    def build_frame(self, tokens):
        
        pass
    
    def parse_faces(self, token):
        
        data = token.get_value()[1]
        stream = NoeBitStream(data)
        
        idxBuff = bytes()
        numFaces = stream.readUInt()
        for i in range(numFaces):
            verts = stream.readUInt()
            idxBuff += stream.readBytes(verts*4)
        self.meshes[-1]["numIdx"] = numFaces * 3
        self.meshes[-1]["idx"] = idxBuff
        
    def parse_vertices(self, token):
        
        numFloats, data = token.get_value()
        self.meshes[-1]["pos"] = data
        
    def assign_normals(self, template):
        
        token = template.get_token()
        token = template.get_token()
        numFloats, data = token.get_value()
        self.meshes[-1]["norms"] = data
        
    def assign_uv(self, template):
        
        token = template.get_token()
        token = template.get_token()
        numFloats, data = token.get_value()
        self.meshes[-1]["uv"] = data
        
    def parse_material_list(self, template):
        
        token = template.get_token()
        if token:
            numInt, data = token.get_value()
            stream = NoeBitStream(data)            
            numMat, numFaces = stream.read('2L')
            matIndexes = stream.read('%dL' %numFaces)
            
            indexes = []
            for i in range(30):            
                count = matIndexes.count(i)
                if not count:
                    break
                indexes.append(count)
            self.meshes[-1]["matIndexes"] = indexes
            
    def parse_material(self, template):
        
        token = template.get_token()
        if token == TOKEN_NAME:
            token = template.get_token()
        numFloats, data = token.get_value()
        
        numMat = len(self.matList)
        matName = "Material[%d]" %numMat
        material = NoeMaterial(matName, "")
        self.matList.append(material)
        
        if self.meshes:
            self.meshes[-1]["materials"].append(matName)
        else:
            self.materials.append(matName)
            
    def parse_texture(self, template):
        
        token = template.get_token()
        if token:
            texName = os.path.basename(token.get_value())
            ext = os.path.splitext(texName)[1]
            texPath = self.dirpath + texName
            if rapi.checkFileExists(texPath):
                f = open(texPath, 'rb')
                tex = rapi.loadTexByHandler(f.read(), ext)
                print(texName, ext)
                if tex is not None:
                    tex.name = texName
                    
                    self.texList.append(tex)
                    self.matList[-1].setTexture(texName)
                f.close()
    
    def parse_mesh(self, template):
        '''Build a mesh from the template'''
        
        #initialize a dict for the mesh object
        self.meshes.append({})
        self.meshes[-1]["materials"] = []
        
        token = template.get_token()
        if token == TOKEN_NAME:
            rapi.rpgSetName(token.get_value())
            token = template.get_token()
        numVerts = token.get_value()[1]
        token = template.get_token()
        self.parse_vertices(token)
        token = template.get_token()
        self.parse_faces(token)
    
    def traverse_templates(self, current, parent):

        templateName = current.name
        if not current.isDefinition:
            if templateName == "Frame":
                self.build_frame(current)
            elif templateName == "Mesh":
                self.parse_mesh(current)
            elif templateName == "MeshNormals":
                self.assign_normals(current)
            elif templateName == "MeshTextureCoords":
                self.assign_uv(current)
            elif templateName == "MeshMaterialList":
                self.parse_material_list(current)
            elif templateName == "Material":
                self.parse_material(current)
            elif templateName == "TextureFilename":
                self.parse_texture(current)
        for template in current.templates:
            self.traverse_templates(template, current)
    
    