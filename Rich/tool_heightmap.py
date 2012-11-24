from inc_noesis import *
import os

HEIGHT_SCALE = 128.0
HEIGHT_DIVISOR = 1
HEIGHT_MAX_DIMENSION = 256
HEIGHT_BLUR = 4.0

def registerNoesisTypes():
	handle = noesis.registerTool("&Heightmesh generator", hmToolMethod)
	return 1

def hmValidateInput(inVal):
	if os.path.exists(inVal) is not True:
		return "'" + inVal + "' does not exist!"
	return None
	
def hmExportFile(heightName):
	saveDefault = rapi.getExtensionlessName(heightName) + "_heightmesh.obj"
	savePath = noesis.userPrompt(noesis.NOEUSERVAL_SAVEFILEPATH, "Save Model", "Select destination for height model.", saveDefault, None)
	if savePath is None:
		return None
	if rapi.toolExportGData(savePath, "") is not True:
		noesis.messagePrompt("Failed to write file.")
		return None
	return savePath
	
def hmToolMethod(toolIndex):
	heightName = noesis.userPrompt(noesis.NOEUSERVAL_FILEPATH, "Open Image", "Select an image to use as a heightmap.", noesis.getSelectedFile(), hmValidateInput)
	if heightName is None:
		return 0
	heightTex = noesis.loadImageRGBA(heightName)
	if heightTex is None:
		noesis.messagePrompt("Failed to load image data from file.")
		return 0
		
	noeMod = noesis.instantiateModule()
	noesis.setModuleRAPI(noeMod)
	
	rgbaPix = rapi.imageGetTexRGBA(heightTex)
	if HEIGHT_BLUR > 0.0:
		rgbaPix = rapi.imageGaussianBlur(rgbaPix, heightTex.width, heightTex.height, HEIGHT_BLUR)

	pointsW = heightTex.width // HEIGHT_DIVISOR
	pointsH = heightTex.height // HEIGHT_DIVISOR
	if pointsW > HEIGHT_MAX_DIMENSION:
		pointsW = HEIGHT_MAX_DIMENSION
	if pointsH > HEIGHT_MAX_DIMENSION:
		pointsH = HEIGHT_MAX_DIMENSION
			
	sizeW = heightTex.width
	sizeH = heightTex.height
	vertCross = ((1, 1), (1, 0), (0, 0), (0, 1))
	ctx = rapi.rpgCreateContext()
	rapi.rpgSetName("heightmesh")
	rapi.rpgSetMaterial(heightName)
	rapi.immBegin(noesis.RPGEO_QUAD_ABC_ACD)
	for y in range(0, pointsH-1):
		for x in range(0, pointsW-1):
			for cross in vertCross:
				fracX = (x+cross[0]) / pointsW
				fracY = (y+cross[1]) / pointsH
				rgba = rapi.imageInterpolatedSample(rgbaPix, heightTex.width, heightTex.height, fracX, fracY)
				z = max(rgba[0], rgba[1], rgba[2])
				rapi.immUV2((fracX, fracY))
				rapi.immVertex3((fracX*sizeW - sizeW*0.5, -fracY*sizeH - sizeH*0.5, z*HEIGHT_SCALE))			
	rapi.immEnd()
	rapi.rpgOptimize()
	mdl = rapi.rpgConstructModel()
	
	rapi.toolSetGData([mdl])
	saveName = hmExportFile(heightName)
	
	rapi.toolFreeGData()
	noesis.freeModule(noeMod)
	
	if saveName is not None:
		noesis.openFile(saveName)
	
	return 0
