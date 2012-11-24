from inc_noesis import *
import noesis
import rapi
import binascii,struct
from Sanae3D.Sanae import SanaeObject
def registerNoesisTypes():
	handle = noesis.register("TitanQuest Texture", ".tex")
	
	
	noesis.setHandlerTypeCheck(handle, noepyCheckType)
	noesis.setHandlerLoadRGBA(handle, noepyLoadRGBA)
	return 1
	
def noepyCheckType(data):
	return 1
	
	
"""FLAGS"""
###CAPS2###
Cubemap = 0x200 
CubemapPositiveX = 0x400  
CubemapNegativeX = 0x800   
CubemapPositiveY = 0x1000  
CubemapNegativeY = 0x2000  
CubemapPositiveZ = 0x4000  
CubemapNegativeZ = 0x8000  
Volume = 0x200000 
###CAPS###
Complex = 0x8
Mipmap = 0x400000 
Texture = 0x1000
###HEADER###
Caps = 0x1            
Height = 0x2          
Width = 0x4           
Pitch = 0x8           
PixelFormat = 0x1000  
MipmapCount = 0x20000 
LinearSize =  0x80000 
Depth =       0x800000
###PIXEL###
AlphaPixels = 0x1
Alpha = 0x2
FourCC = 0x4
PaletteIndexed8 = 0x20
RGB = 0x40
YUV = 0x200
Luminance = 0x20000
###VARIANT###
Reversed = 0x52
Default = 0x20


class DDS:
	def __init__(self, data):
		self.header = self.header(data)
		self.header.Images,self.header.Layers = self.parseMipmap(data)
		self.FixHeader()

	class header:
		def __init__(self,data):
			self.DDS = data.read("3c")
			self.Version = data.read("b")[0]
			self.DefaultSize = data.readUInt()
			if self.DefaultSize != 124: raise ValueError("HeaderDS != 124")
			self.Flags = data.readUInt()
			self.Height = data.readUInt()
			self.Width = data.readUInt()
			self.LinearSize = data.readUInt()
			self.Depth = data.readUInt()
			self.MipmapCount = data.readUInt()
			self.Reserved1 = data.read('11i')
			self.PixelFormat = self.pixelFormat(data)
			self.Caps = data.readUInt()
			self.Caps2= data.readUInt()
			self.Caps3 = data.readUInt()
			self.Caps4 = data.readUInt()
			self.Reserved2 = data.readUInt()
		class pixelFormat:
			def __init__(self,data):
				self.DefaultSize = data.readUInt()
				if self.DefaultSize != 32: raise ValueError("DS != 32")
				self.Flags = data.readUInt()
				self.FourCC =noeStrFromBytes(data.readBytes(4))
				self.RGBBitCount = data.readUInt()
				self.RBitMask = data.readUInt()
				self.GBitMask = data.readUInt()
				self.BBitMask = data.readUInt()
				self.ABitMask = data.readUInt()

		
	def FixHeader(self):
		self.header.Flags |= Caps | Height | Width | PixelFormat
		self.header.Caps  |= Texture
		self.header.MipmapCount = len(self.header.Images[0])
		
		if self.header.MipmapCount >1:
			self.header.Flags |= MipmapCount
			self.header.Caps |= Complex | Mipmap
			
		if self.header.Caps2 & Cubemap:
			self.header.Caps |= Complex
			
		if self.header.Depth >1:
			self.header.Caps |= Complex
			self.header.Flags |= Depth
			
		if (self.header.PixelFormat.Flags & FourCC) and self.header.LinearSize != 0:
			self.header.Flags |= LinearSize
			
		if (self.header.PixelFormat.Flags & RGB or self.header.PixelFormat.Flags & YUV or self.header.PixelFormat.Flags & Luminance or self.header.PixelFormat.Flags & Alpha) and self.header.LinearSize !=0:
			self.header.Flags |= Pitch
			
		if self.header.PixelFormat.Flags & RGB and (self.header.PixelFormat.RBitMask +self.header.PixelFormat.GBitMask +self.header.PixelFormat.GBitMask ==0):
			self.header.PixelFormat.RBitMask = 0xff0000
			self.header.PixelFormat.GBitMask = 0x00ff00
			self.header.PixelFormat.BBitMask = 0x0000ff
		
	def Reverse(self,array):
		if self.header.Version == Reversed:
			self.header.Version = Default
			return
		elif self.header.Version == Default:
			self.header.Version = Reversed
			return
	def parseMipmap(self,data):
		layers = 1
		if self.header.Caps2 & Cubemap:
			layers = 0
			if self.header.Caps2 & CubemapPositiveX: layers +=1
			if self.header.Caps2 & CubemapNegativeX: layers +=1
			if self.header.Caps2 & CubemapPositiveY: layers +=1
			if self.header.Caps2 & CubemapNegativeY: layers +=1
			if self.header.Caps2 & CubemapPositiveZ: layers +=1
			if self.header.Caps2 & CubemapNegativeZ: layers +=1
		mipcount = self.header.MipmapCount
		if mipcount ==0 and (self.header.Flags & MipmapCount): mipcount = 1
		lengths=[]
		mips = []
		for i in range(mipcount):
			height = self.header.Height
			width  = self.header.Width
			
			for t in range(i):
				width = width//2
				height= height //2
			if height <1: height = 1
			if width <1: width = 1
			if "DXT" in self.header.PixelFormat.FourCC:
				if width %4 != 0:
					# print("w %d: %d"%(width,width%4))
					width +=4 - (width%4)
					
				if height %4 != 0:
					# print("h %d: %d"%(height,height%4))
					height +=4 -(height%4)
				if self.header.PixelFormat.FourCC == "DXT1":
					lengths.append(width*height//2)
				else:
					lengths.append(width*height)
			
			elif self.header.PixelFormat.RGBBitCount != 0:
				lengths.append(width*height*self.header.PixelFormat.RGBBitCount)
				if lengths[i] //8 != 0:
					lengths[i] += 8 - (lengths[i] //8)
				lengths[i] = lengths[i]//8
			# print(width,height)
		# print(lengths)
		if self.header.Version == Reversed:
			lengths.reverse()
		# print(lengths)
		for i in range(layers):
			mips.append([])
			# mips[i] = []
			for t in range(mipcount):
				
				mips[i].append(data.readBytes(lengths[t]))
		#print(len(mips[0][10]))
		return mips,layers
	def WriteFixedDDS(self):
		file=NoeBitStream()
		file.writeBytes(b"\x44\x44\x53\x20")
		file.writeBytes(noePack("<1i",self.header.DefaultSize))
		file.writeBytes(noePack("<1i",self.header.Flags))
		file.writeBytes(noePack("<1i",self.header.Height))
		file.writeBytes(noePack("<1i",self.header.Width))
		file.writeBytes(noePack("<1i",self.header.LinearSize))
		file.writeBytes(noePack("<1i",self.header.Depth))
		file.writeBytes(noePack("<1i",self.header.MipmapCount))
		file.writeBytes(noePack("<11i",*self.header.Reserved1))
		file.writeBytes(noePack("<1i",self.header.PixelFormat.DefaultSize))
		file.writeBytes(noePack("<1i",self.header.PixelFormat.Flags))
		if "DXT" in self.header.PixelFormat.FourCC:
			file.writeBytes(b"\x44\x58\x54") #write "DXT"
			file.writeBytes(struct.pack('b',48+int(self.header.PixelFormat.FourCC[-1]))) #write 1-5
		else:
			file.writeBytes(b"\x00\x00\x00\x00")
		file.writeBytes(noePack("<1i",self.header.PixelFormat.RGBBitCount))
		file.writeBytes(noePack("<1i",self.header.PixelFormat.RBitMask))
		file.writeBytes(noePack("<1i",self.header.PixelFormat.GBitMask))
		file.writeBytes(noePack("<1i",self.header.PixelFormat.BBitMask))
		try:file.writeBytes(noePack("<1i",self.header.PixelFormat.ABitMask))
		except: file.writeBytes(b"\x00\x00\x00\xFF")
		file.writeBytes(noePack("<1i",self.header.Caps))
		file.writeBytes(noePack("<1i",self.header.Caps2))
		file.writeBytes(noePack("<1i",self.header.Caps3))
		file.writeBytes(noePack("<1i",self.header.Caps4))
		file.writeBytes(noePack("<1i",self.header.Reserved2))
		self.header.Images[0].reverse()
		for l in range(self.header.Layers):
			for m in range(self.header.MipmapCount):
				file.writeBytes(self.header.Images[l][m])
		return file
class TexFile:
	def __init__(self,data):
		self.data = data.read('3i')
		

	
def noepyLoadRGBA(data,texList):
	Data = NoeBitStream(data)
	texfile = TexFile(Data)
	dds = DDS(Data)
	if dds.header.Version == Reversed:
		q=dds.WriteFixedDDS()
		q=q.getBuffer()
	else:
		Data = NoeBitStream(data)
		Data.readBytes(12)
		q=Data.getBuffer()
		q=q[12:]
	tex = rapi.loadTexByHandler(q, '.dds')
	if tex: texList.append(tex)
	# texList.append(NoeTexture("TQTex",dds.header.Width,dds.header.Height,dds.header.Images[0][9],noesis.NOESISTEX_DXT5))
	return 1