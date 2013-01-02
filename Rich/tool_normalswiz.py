from inc_noesis import *
import os

def registerNoesisTypes():
	handle = noesis.registerTool("&Normal swizzler", nswzToolMethod)
	return 1

def nswzValidateInput(inVal):
	if os.path.exists(inVal) is not True:
		return "'" + inVal + "' does not exist!"
	return None
	
def nswzToolMethod(toolIndex):
	srcName = noesis.userPrompt(noesis.NOEUSERVAL_FILEPATH, "Open Image", "Select an image to swizzle.", noesis.getSelectedFile(), nswzValidateInput)
	if srcName is None:
		return 0
	srcTex = noesis.loadImageRGBA(srcName)
	if srcTex is None:
		noesis.messagePrompt("Failed to load image data from file.")
		return 0

	dstDefault = os.path.splitext(srcName)[0] + ".png"
	dstName = noesis.userPrompt(noesis.NOEUSERVAL_SAVEFILEPATH, "Save Image", "Select destination path for the swizzled image.", dstDefault, None)
	if dstName is None:
		return None

	noeMod = noesis.instantiateModule()
	noesis.setModuleRAPI(noeMod)
	
	rgbaPix = rapi.imageGetTexRGBA(srcTex)
	dstTex = NoeTexture(dstName, srcTex.width, srcTex.height, rapi.imageNormalSwizzle(rgbaPix, srcTex.width, srcTex.height, 1, 1, 0), noesis.NOESISTEX_RGBA32)

	noesis.freeModule(noeMod)

	if noesis.saveImageRGBA(dstName, dstTex) is not True:
		noesis.messagePrompt("Error writing swizzled image.")
		return 0

	noesis.openFile(dstName)
	return 0
