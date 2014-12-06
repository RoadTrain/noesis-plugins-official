from inc_noesis import *
import os

FLIP_UV_ON_EXPORT = True

def registerNoesisTypes():
	handle = noesis.registerTool("Reprocess and apply material", gmToolMethod, "Load a model, apply a named material to the whole thing, and re-export.")
	noesis.setToolFlags(handle, noesis.NTOOLFLAG_CONTEXTITEM)
	noesis.setToolVisibleCallback(handle, gmContextVisible)
	return 1

def gmContextVisible(toolIndex, selectedFile):
	if selectedFile is None or (noesis.getFormatExtensionFlags(os.path.splitext(selectedFile)[1]) & noesis.NFORMATFLAG_MODELREAD) == 0:
		return 0
	return 1
	
def gmToolMethod(toolIndex):
	newMtlName = noesis.userPrompt(noesis.NOEUSERVAL_STRING, "New Material", "Enter the material name to apply.", "defaultmaterial", None)
	if newMtlName is not None:
		selectedFile = noesis.getSelectedFile()
		if selectedFile is not None:
			noeMod = noesis.instantiateModule()
			noesis.setModuleRAPI(noeMod)
			
			rapi.toolLoadGData(selectedFile)
			if rapi.toolGetLoadedModelCount() <= 0:
				noesis.messagePrompt("Could not load any models from " + selectedFile)
			else:
				#get the first loaded model, then run through and set material names.
				#we don't bother actually defining the materials on the model, material
				#names will be used by default to load diffuse maps.
				mdl = rapi.toolGetLoadedModel(0)
				for mesh in mdl.meshes:
					mesh.setMaterial(newMtlName)
				rapi.toolSetGData([mdl])
				
				saveDefault = rapi.getExtensionlessName(selectedFile) + "_withmaterials.obj"
				savePath = noesis.userPrompt(noesis.NOEUSERVAL_SAVEFILEPATH, "Save Model", "Select destination for new model.", saveDefault, None)
				if savePath is not None:
					exportOptions = "-flipuv" if FLIP_UV_ON_EXPORT else ""
					if rapi.toolExportGData(savePath, exportOptions) is not True:
						noesis.messagePrompt("Failed to write file.")
		
				rapi.toolFreeGData()
				
			noesis.freeModule(noeMod)
		
	return 0
