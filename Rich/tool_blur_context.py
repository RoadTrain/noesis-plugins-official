from inc_noesis import *
import os

GAUSSIAN_BLUR_DEFAULT = 8.0

def registerNoesisTypes():
	handle = noesis.registerTool("&Gaussian blur", gbToolMethod, "Perform Gaussian blur on the image")
	noesis.setToolFlags(handle, noesis.NTOOLFLAG_CONTEXTITEM)
	noesis.setToolVisibleCallback(handle, gbContextVisible)
	return 1

def gbContextVisible(toolIndex, selectedFile):
	if selectedFile is None or (noesis.getFormatExtensionFlags(os.path.splitext(selectedFile)[1]) & noesis.NFORMATFLAG_IMGREAD) == 0:
		return 0
	return 1

def gbValidateBlur(inVal):
	if inVal < 0.0 or inVal > 100.0:
		return "Value must be between 0 and 100."
	return None
	
def gbToolMethod(toolIndex):
	srcName = noesis.getSelectedFile()
	if srcName is None or os.path.exists(srcName) is not True:
		noesis.messagePrompt("Selected file isn't readable through the standard filesystem.")
		return 0

	srcTex = noesis.loadImageRGBA(srcName)
	if srcTex is None:
		noesis.messagePrompt("Failed to load image data from file.")
		return 0
		
	global GAUSSIAN_BLUR_DEFAULT
	blurAmount = noesis.userPrompt(noesis.NOEUSERVAL_FLOAT, "Blur Amount", "Enter gaussian blur amount.", repr(GAUSSIAN_BLUR_DEFAULT), gbValidateBlur)
	if blurAmount is None:
		return 0
	GAUSSIAN_BLUR_DEFAULT = blurAmount

	noeMod = noesis.instantiateModule()
	noesis.setModuleRAPI(noeMod)
	
	dstName = noesis.getScenesPath() + "plugindata_blurresult.png"
	
	rgbaPix = rapi.imageGetTexRGBA(srcTex)
	dstTex = NoeTexture(dstName, srcTex.width, srcTex.height, rapi.imageGaussianBlur(rgbaPix, srcTex.width, srcTex.height, blurAmount), noesis.NOESISTEX_RGBA32)

	noesis.freeModule(noeMod)

	if noesis.saveImageRGBA(dstName, dstTex) is not True:
		noesis.messagePrompt("Error writing blurred image.")
		return 0
	
	noesis.openAndRemoveTempFile(dstName)
	return 0
