from inc_noesis import *
from bs4 import BeautifulSoup

def registerNoesisTypes():
	handle = noesis.register("Noesis Cubemap", ".noecube")
	noesis.setHandlerTypeCheck(handle, noeCubeCheckType)
	noesis.setHandlerLoadRGBA(handle, noeCubeLoadRGBA)
	return 1

def noeCubeCheckType(data):
	try:
		xmlText = noeStrFromBytes(data)
		soup = BeautifulSoup(xmlText)
		if soup.noesis_cubemap is not None:
			return 1
	except:
		pass
	return 0

def noeCubeLoadRGBA(data, texList):
	basePath = rapi.getDirForFilePath(rapi.getLastCheckedName())
	xmlText = noeStrFromBytes(data)
	soup = BeautifulSoup(xmlText)
	imgList = [None]*6
	width = -1
	height = -1
	oriMap = {"posx":0, "negx":1, "posy":2, "negy":3, "posz":4, "negz":5}
	imgName = soup.noesis_cubemap.get("name")
	if imgName is None:
		imgName = "cubeimage"

	for image in soup.noesis_cubemap.find_all("image"):
		imgName = image.get("name")
		imgOri = image.get("ori")
		if imgName is None or imgOri is None:
			print("WARNING: Badly formatted image:", image)
			continue
		if imgOri not in oriMap:
			print("WARNING: Unknown image type:", imgOri)
			continue
		tex = rapi.loadExternalTex(basePath + "\\" + imgName)
		if tex is None:
			print("WARNING: Could not load image:", imgName)
			continue
		if tex.width <= 0 or tex.height <= 0:
			print("WARNING: Bad image dimensions on image:", imgName)
			continue
		rgba = rapi.imageGetTexRGBA(tex)
		if rgba is None:
			print("WARNING: Could not get RGBA data for image:", imgName)
			continue
		if width <= 0 or height <= 0:
			width = tex.width
			height = tex.height
		elif width != tex.width or height != tex.height: #auto-resize subsequent images so that they're all the same size
			rgba = rapi.imageResample(rgba, tex.width, tex.height, width, height)
		imgList[oriMap[imgOri]] = rgba

	if width <= 0 or height <= 0:
		print("ERROR: Could not load any images.")
		return 0

	cubePixels = bytearray()
	for i in range(0, 6):
		if imgList[i] is None: #fill with white pixels
			cubePixels += bytearray([255]*width*height*4)
		else:
			cubePixels += imgList[i]
	tex = NoeTexture(imgName, width, height, cubePixels)
	tex.setFlags(noesis.NTEXFLAG_CUBEMAP)
	texList.append(tex)
	return 1
