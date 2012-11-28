from inc_noesis import *
import os

GAUSSIAN_BLUR_DEFAULT = 8.0

def registerNoesisTypes():
	handle = noesis.registerTool("&Gaussian blur", gbToolMethod, "Invoke Gaussian blur script")
	return 1

def gbValidateInput(inVal):
	if os.path.exists(inVal) is not True:
		return "'" + inVal + "' does not exist!"
	return None
	
def gbValidateBlur(inVal):
	if inVal < 0.0 or inVal > 100.0:
		return "Value must be between 0 and 100."
	return None
	
def gbToolMethod(toolIndex):
	srcName = noesis.userPrompt(noesis.NOEUSERVAL_FILEPATH, "Open Image", "Select an image to blur.", noesis.getSelectedFile(), gbValidateInput)
	if srcName is None:
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
		
	dstDefault = os.path.splitext(srcName)[0] + "_blurred.png"
	dstName = noesis.userPrompt(noesis.NOEUSERVAL_SAVEFILEPATH, "Save Image", "Select destination path for the blurred image.", dstDefault, None)
	if dstName is None:
		return None

	noeMod = noesis.instantiateModule()
	noesis.setModuleRAPI(noeMod)
	
	rgbaPix = rapi.imageGetTexRGBA(srcTex)
	dstTex = NoeTexture(dstName, srcTex.width, srcTex.height, rapi.imageGaussianBlur(rgbaPix, srcTex.width, srcTex.height, blurAmount), noesis.NOESISTEX_RGBA32)

	noesis.freeModule(noeMod)

	if noesis.saveImageRGBA(dstName, dstTex) is not True:
		noesis.messagePrompt("Error writing blurred image.")
		return 0
	
	noesis.openFile(dstName)
	return 0
