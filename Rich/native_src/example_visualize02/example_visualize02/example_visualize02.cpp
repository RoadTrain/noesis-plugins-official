// example_visualize02.cpp : Defines the entry point for the DLL application.
//

#include "stdafx.h"
#include <gl/gl.h>
#include <math.h>

mathImpFn_t *g_mfn = NULL;
noePluginFn_t *g_nfn = NULL;

#ifdef _MANAGED
#pragma managed(push, off)
#endif

#define PICKFLAG_SELECTED		(1<<0)
typedef struct pickerMesh_s
{
	int					*triFlags;
} pickerMesh_t;

typedef struct pickerMdl_s
{
	pickerMesh_t		*meshes;
} pickerMdl_t;

static bool g_visualizing = false;
static int g_vh = -1;

static sharedModel_t *g_smdl = NULL;
static int g_smdlIdx = -1;
static pickerMdl_t g_pickMdl;
static bool g_useSkin = false;

static int g_checkRayX = -1;
static int g_checkRayY = -1;
static int g_checkRaySelect = 0;
static int g_firstDown = 0;
static int g_hitMeshIdx = -1;
static int g_hitFaceIdx = -1;
static int g_numFaceSel = 0;
static bool g_buttonsRegistered = false;

//shared model should never be loaded when a new model is loaded
static void OnModelLoaded(int vh)
{
	assert(!g_smdl);
	assert(!g_pickMdl.meshes);
}

//free the shared model if one is loaded
static void FreeSharedModel(void)
{
	noeRAPI_t *rapi = g_nfn->NPAPI_GetPreviewRAPI();
	if (g_smdl)
	{
		if (rapi)
		{
			rapi->Noesis_FreeSharedModel(g_smdl);
		}
		g_smdl = NULL;
	}
	if (g_pickMdl.meshes)
	{
		rapi->Noesis_UnpooledFree(g_pickMdl.meshes);
	}
	memset(&g_pickMdl, 0, sizeof(pickerMdl_t));
	g_smdlIdx = -1;
	g_useSkin = false;
	g_checkRayX = -1;
	g_checkRayY = -1;
	g_checkRaySelect = 0;
	g_firstDown = 0;
	g_hitMeshIdx = -1;
	g_hitFaceIdx = -1;
	g_numFaceSel = 0;
}

//called on preview model close
static void OnModelClose(int vh)
{
	FreeSharedModel();
	g_buttonsRegistered = false;
}

//called on preview model reset
static void OnModelReset(int vh)
{
	FreeSharedModel();
}

//see if anything is selected
static bool CanExportTriangles(void)
{
	if (!g_smdl)
	{
		return false;
	}
	for (int i = 0; i < g_smdl->numMeshes; i++)
	{
		sharedMesh_t *mesh = g_smdl->meshes+i;
		if (!mesh->tris || !mesh->verts)
		{
			continue;
		}
		pickerMesh_t *pmesh = g_pickMdl.meshes+i;
		for (int j = 0; j < mesh->numTris; j++)
		{
			if (pmesh->triFlags[j] & PICKFLAG_SELECTED)
			{
				return true;
			}
		}
	}
	return false;
}

//validate the given export path
char *ValidateExportPath(void *valIn, noeUserValType_e valInType)
{
	if (valInType != NOEUSERVAL_SAVEFILEPATH)
	{
		return "Unexpected parameter type.";
	}
	wchar_t *path = (wchar_t *)valIn;
	if (!path[0])
	{
		return "You must enter a valid file path.";
	}
	return NULL;
}

//button callback
static void ExportSelectionUse(void)
{
	if (!CanExportTriangles())
	{
		g_nfn->NPAPI_MessagePrompt(L"No triangles are selected to export.");
		return;
	}
	noeRAPI_t *prvRapi = g_nfn->NPAPI_GetPreviewRAPI();
	if (!prvRapi)
	{
		return;
	}

	int mod = g_nfn->NPAPI_InstantiateModule(NULL);
	if (mod < 0)
	{
		return;
	}
	noeRAPI_t *rapi = g_nfn->NPAPI_GetModuleRAPI(mod);
	assert(rapi);
	void *pgctx = rapi->rpgCreateContext();
	for (int i = 0; i < g_smdl->numMeshes; i++)
	{
		sharedMesh_t *mesh = g_smdl->meshes+i;
		if (!mesh->tris || !mesh->verts)
		{
			continue;
		}
		modelVert_t *verts = (g_useSkin && mesh->transVerts) ? mesh->transVerts : mesh->verts;
		modelVert_t *normals = (g_useSkin && mesh->transNormals) ? mesh->transNormals : mesh->normals;
		pickerMesh_t *pmesh = g_pickMdl.meshes+i;
		rapi->rpgSetName(mesh->name);
		rapi->rpgSetMaterial(mesh->skinName);
		for (int j = 0; j < mesh->numTris; j++)
		{
			if (!(pmesh->triFlags[j] & PICKFLAG_SELECTED))
			{
				continue;
			}
			WORD *idxs = &mesh->tris[j].a;
			rapi->rpgBegin(RPGEO_TRIANGLE);
			for (int k = 0; k < 3; k++)
			{
				WORD idx = idxs[k];
				if (mesh->colors)
				{
					rapi->rpgVertColor4f(mesh->colors[idx].rgba);
				}
				else
				{
					rapi->rpgVertColor4f(NULL);
				}
				if (mesh->uvs)
				{
					rapi->rpgVertUV2f(&mesh->uvs[idx].u, 0);
				}
				else
				{
					rapi->rpgVertUV2f(NULL, 0);
				}
				if (normals)
				{
					rapi->rpgVertNormal3f(&normals[idx].x);
				}
				else
				{
					rapi->rpgVertNormal3f(NULL);
				}
				rapi->rpgVertex3f(&verts[idx].x);
			}
			rapi->rpgEnd();
		}
	}

	noesisModel_t *mdl = rapi->rpgConstructModel();
	rapi->rpgDestroyContext(pgctx);
	if (mdl)
	{
		char defPath[MAX_NOESIS_PATH];
		prvRapi->Noesis_GetExtensionlessName(defPath, prvRapi->Noesis_GetInputName());
		strcat_s(defPath, MAX_NOESIS_PATH, "_tricut.obj");
		rapi->Noesis_SetGData(mdl, 1);
		noeUserPromptParam_t parms;
		memset(&parms, 0, sizeof(noeUserPromptParam_t));
		parms.titleStr = "Save Model";
		parms.promptStr = "Select destination file for exported triangles.";
		parms.valHandler = ValidateExportPath;
		parms.valType = NOEUSERVAL_SAVEFILEPATH;
		parms.defaultValue = defPath;
		if (g_nfn->NPAPI_UserPrompt(&parms))
		{
			wchar_t saveName[MAX_NOESIS_PATH];
			wcscpy_s(saveName, MAX_NOESIS_PATH, (wchar_t *)parms.valBuf);
			if (!rapi->Noesis_CheckFileExtW(saveName, L".obj"))
			{
				wcscat_s(saveName, MAX_NOESIS_PATH, L".obj");
			}
			if (!rapi->Noesis_ExportGData(saveName, ""))
			{
				wchar_t err[MAX_NOESIS_PATH];
				swprintf_s(err, MAX_NOESIS_PATH, L"Error writing '%s'!", saveName);
				g_nfn->NPAPI_MessagePrompt(err);
			}
		}
		rapi->Noesis_FreeGData();
	}

	g_nfn->NPAPI_FreeModule(mod);
}

//button visibility check
static bool ExportSelectionVisible(void *resv)
{
	return g_visualizing;
}

//locally load a shared model for the selected model in the preview
static bool PreRender(int vh, void *resv, noeSharedGL_t *ngl)
{
	noeRAPI_t *rapi = g_nfn->NPAPI_GetPreviewRAPI();
	if (!rapi)
	{
		return true;
	}

	if (!g_buttonsRegistered)
	{
		rapi->Noesis_RegisterUserButton(NULL, NULL, 0, 0, ExportSelectionUse, ExportSelectionVisible, "Export selected triangles",
			NULL, NULL, NULL, NULL);
		g_buttonsRegistered = true;
	}

	int mdlIdx = rapi->Noesis_GetSelectedPreviewModel();
	if (mdlIdx < 0)
	{
		return true;
	}
	if (g_smdlIdx != mdlIdx)
	{
		FreeSharedModel();
	}

	if (!g_smdl)
	{ //re-grab shared model data
		noesisModel_t *mdl = rapi->Noesis_GetLoadedModel(mdlIdx);
		if (!mdl)
		{
			return true;
		}
		sharedModel_t *smdl = rapi->rpgGetSharedModel(mdl, NMSHAREDFL_LOCALPOOL);
		if (!smdl)
		{
			return true;
		}
		g_smdl = smdl;
		g_smdlIdx = mdlIdx;
		//allocate the picker model data
		int totalTris = 0;
		for (int i = 0; i < g_smdl->numMeshes; i++)
		{
			sharedMesh_t *mesh = g_smdl->meshes+i;
			totalTris += mesh->numTris;
		}
		int totalSize = sizeof(int)*totalTris + sizeof(pickerMesh_t)*g_smdl->numMeshes;
		g_pickMdl.meshes = (pickerMesh_t *)rapi->Noesis_UnpooledAlloc(totalSize);
		memset(g_pickMdl.meshes, 0, totalSize);
		int *triMem = (int *)(g_pickMdl.meshes+g_smdl->numMeshes);
		for (int i = 0; i < g_smdl->numMeshes; i++)
		{
			sharedMesh_t *mesh = g_smdl->meshes+i;
			pickerMesh_t *pmesh = g_pickMdl.meshes+i;
			pmesh->triFlags = triMem;
			triMem += mesh->numTris;
		}
	}

	return true;
}

//do a ray test
static void ModelRayCheck(int x, int y, noeSharedGL_t *ngl, int &hitMeshIdx, int &hitTriIdx)
{
	assert(g_smdl);
	float modelView[16];
	float projection[16];
	float mvp[16];
	ngl->NGL_GetFloat(GL_MODELVIEW_MATRIX, modelView);
	ngl->NGL_GetFloat(GL_PROJECTION_MATRIX, projection);
	g_mfn->Math_MatrixMultiply4x4((fourxMatrix_t *)modelView, (fourxMatrix_t *)projection, (fourxMatrix_t *)mvp);

	float screenW, screenH;
	ngl->NGL_GetResolution(screenW, screenH);

	float screenStart[3] = {(float)x, (float)y, 0.0f};
	float screenEnd[3] = {(float)x, (float)y, 0.9999f};
	float worldStart[3], worldEnd[3], worldDir[3];

	g_mfn->Math_ScreenToWorldSpace(mvp, screenW, screenH, screenStart, worldStart);
	g_mfn->Math_ScreenToWorldSpace(mvp, screenW, screenH, screenEnd, worldEnd);
	g_mfn->Math_VecSub(worldEnd, worldStart, worldDir);
	g_mfn->Math_VecNorm(worldDir);

	hitMeshIdx = -1;
	hitTriIdx = -1;
	float bestDist = 0.0f;
	//lots of optimizations could be put in place here. (transformed bounds for meshes should be checked, or implement a better transformable scene graph,
	//cull out backfaces, planes can be transformed or precalculated if not skinning, etc)
	for (int i = 0; i < g_smdl->numMeshes; i++)
	{
		sharedMesh_t *mesh = g_smdl->meshes+i;
		modelVert_t *verts = (g_useSkin && mesh->transVerts) ? mesh->transVerts : mesh->verts;
		for (int j = 0; j < mesh->numTris; j++)
		{
			modelTriFace_t *tri = mesh->tris+j;
			modelVert_t *v1 = verts+tri->a;
			modelVert_t *v2 = verts+tri->b;
			modelVert_t *v3 = verts+tri->c;
			float plane[4];
			g_mfn->Math_PlaneFromPoints(&v1->x, &v2->x, &v3->x, plane);
			float hitDist;
			if (g_mfn->Math_LineIntersectTri(worldStart, worldEnd, worldDir, &v1->x, &v2->x, &v3->x, plane, &hitDist))
			{
				if (hitMeshIdx == -1 || hitDist < bestDist)
				{
					hitMeshIdx = i;
					hitTriIdx = j;
					bestDist = hitDist;
				}
			}
		}
	}
}

//custom rendering of the shared model
static void PostRender(int vh, modelMatrix_t *skinMats, int numSkinMats, float animFrame, void *resv, noeSharedGL_t *ngl)
{
	if (!g_smdl)
	{
		return;
	}
	noeRAPI_t *rapi = g_nfn->NPAPI_GetPreviewRAPI();
	if (!rapi)
	{
		return;
	}
	g_useSkin = rapi->Noesis_CopyInternalTransforms(g_smdl);

	if (g_checkRayX >= 0 && g_checkRayY >= 0)
	{
		ModelRayCheck(g_checkRayX, g_checkRayY, ngl, g_hitMeshIdx, g_hitFaceIdx);
		if (g_firstDown == 1)
		{
			if (g_hitMeshIdx >= 0 && g_hitFaceIdx >= 0)
			{
				g_firstDown = 2;
			}
			else
			{
				g_firstDown = -1;
			}
		}
		if (g_checkRaySelect)
		{
			if (g_hitMeshIdx >= 0 && g_hitFaceIdx >= 0)
			{
				if (g_checkRaySelect == 2)
				{
					if (g_pickMdl.meshes[g_hitMeshIdx].triFlags[g_hitFaceIdx] & PICKFLAG_SELECTED)
					{
						g_pickMdl.meshes[g_hitMeshIdx].triFlags[g_hitFaceIdx] &= ~PICKFLAG_SELECTED;
						g_numFaceSel--;
					}
				}
				else
				{
					if (!(g_pickMdl.meshes[g_hitMeshIdx].triFlags[g_hitFaceIdx] & PICKFLAG_SELECTED))
					{
						g_pickMdl.meshes[g_hitMeshIdx].triFlags[g_hitFaceIdx] |= PICKFLAG_SELECTED;
						g_numFaceSel++;
					}
				}
			}
			g_checkRaySelect = 0;
		}
		g_checkRayX = -1;
		g_checkRayY = -1;
	}

	ngl->NGL_BindTexture(NULL);
	ngl->NGL_Disable(GL_CULL_FACE);
	ngl->NGL_LineWidth(3.0f);

	if (g_numFaceSel > 0)
	{ //to 2 separate loops for triangles and outlines so that batches aren't interrupted
		ngl->NGL_Color4f(1.0f, 0.25f, 0.25f, 1.0f);
		ngl->NGL_Begin(NGL_PRIM_TRIANGLES);
		for (int i = 0; i < g_smdl->numMeshes; i++)
		{
			sharedMesh_t *mesh = g_smdl->meshes+i;
			modelVert_t *verts = (g_useSkin && mesh->transVerts) ? mesh->transVerts : mesh->verts;
			pickerMesh_t *pmesh = g_pickMdl.meshes+i;
			for (int j = 0; j < mesh->numTris; j++)
			{
				if (!(pmesh->triFlags[j] & PICKFLAG_SELECTED))
				{
					continue;
				}
				modelTriFace_t *tri = mesh->tris+j;
				ngl->NGL_Vertex3fv(&verts[tri->a].x);
				ngl->NGL_Vertex3fv(&verts[tri->b].x);
				ngl->NGL_Vertex3fv(&verts[tri->c].x);
			}
		}
		ngl->NGL_End();
		ngl->NGL_Color4f(0.0f, 0.0f, 0.0f, 1.0f);
		ngl->NGL_Begin(NGL_PRIM_LINES);
		for (int i = 0; i < g_smdl->numMeshes; i++)
		{
			sharedMesh_t *mesh = g_smdl->meshes+i;
			modelVert_t *verts = (g_useSkin && mesh->transVerts) ? mesh->transVerts : mesh->verts;
			pickerMesh_t *pmesh = g_pickMdl.meshes+i;
			for (int j = 0; j < mesh->numTris; j++)
			{
				if (!(pmesh->triFlags[j] & PICKFLAG_SELECTED))
				{
					continue;
				}
				modelTriFace_t *tri = mesh->tris+j;
				ngl->NGL_Vertex3fv(&verts[tri->a].x);
				ngl->NGL_Vertex3fv(&verts[tri->b].x);
				ngl->NGL_Vertex3fv(&verts[tri->b].x);
				ngl->NGL_Vertex3fv(&verts[tri->c].x);
				ngl->NGL_Vertex3fv(&verts[tri->c].x);
				ngl->NGL_Vertex3fv(&verts[tri->a].x);
			}
		}
		ngl->NGL_End();
	}

	if (g_hitMeshIdx >= 0 && g_hitFaceIdx >= 0)
	{ //draw the highlighted tri
		sharedMesh_t *mesh = g_smdl->meshes+g_hitMeshIdx;
		modelTriFace_t *tri = mesh->tris+g_hitFaceIdx;
		modelVert_t *verts = (g_useSkin && mesh->transVerts) ? mesh->transVerts : mesh->verts;
		ngl->NGL_Color4f(0.0f, 1.0f, 0.0f, 1.0f);
		ngl->NGL_Begin(NGL_PRIM_TRIANGLES);
			ngl->NGL_Vertex3fv(&verts[tri->a].x);
			ngl->NGL_Vertex3fv(&verts[tri->b].x);
			ngl->NGL_Vertex3fv(&verts[tri->c].x);
		ngl->NGL_End();
		ngl->NGL_Color4f(1.0f, 1.0f, 1.0f, 1.0f);
		ngl->NGL_Begin(NGL_PRIM_LINES);
			ngl->NGL_Vertex3fv(&verts[tri->a].x);
			ngl->NGL_Vertex3fv(&verts[tri->b].x);
			ngl->NGL_Vertex3fv(&verts[tri->b].x);
			ngl->NGL_Vertex3fv(&verts[tri->c].x);
			ngl->NGL_Vertex3fv(&verts[tri->c].x);
			ngl->NGL_Vertex3fv(&verts[tri->a].x);
		ngl->NGL_End();
	}

	ngl->NGL_LineWidth(1.0f);
	ngl->NGL_Enable(GL_CULL_FACE);
}

//process new input
static bool GotInput(int vh, int x, int y, int buttonFlags, void *resv)
{
	if (buttonFlags & NOESISBUTTON_MOUSEEXIT)
	{
		g_checkRayX = -1;
		g_checkRayY = -1;
		g_checkRaySelect = 0;
		g_hitMeshIdx = -1;
		g_hitFaceIdx = -1;
		return true;
	}

	if (!(buttonFlags & NOESISBUTTON_LBUTTON))
	{
		g_firstDown = 0;
	}

	if (!(buttonFlags & NOESISBUTTON_NOCURSOR))
	{
		g_checkRayX = x;
		g_checkRayY = y;
		if (buttonFlags & NOESISBUTTON_LBUTTON)
		{
			if (g_firstDown == 0)
			{
				g_firstDown = 1;
			}
		}

		if (g_firstDown > 0)
		{
			g_checkRaySelect = (buttonFlags & NOESISBUTTON_CONTROL) ? 2 : 1;
		}
	}

	if (g_firstDown > 0 && (buttonFlags & NOESISBUTTON_LBUTTON))
	{
		return false;
	}
	return true;
}

//toggle the visualizer
static int Visualizer_Invoke(int toolIdx, void *userData)
{
	g_visualizing = !g_visualizing;
	g_nfn->NPAPI_CheckToolMenuItem(toolIdx, g_visualizing);

	if (g_vh >= 0)
	{
		if (g_visualizing)
		{
			g_nfn->NPAPI_Visualizer_SetPreRender(g_vh, PreRender);
			g_nfn->NPAPI_Visualizer_SetPostRender(g_vh, PostRender);
			g_nfn->NPAPI_Visualizer_SetInput(g_vh, GotInput);
		}
		else
		{
			g_nfn->NPAPI_Visualizer_SetPreRender(g_vh, NULL);
			g_nfn->NPAPI_Visualizer_SetPostRender(g_vh, NULL);
			g_nfn->NPAPI_Visualizer_SetInput(g_vh, NULL);
			FreeSharedModel();
		}
	}
	return 0;
}

//called by Noesis to init the plugin
NPLUGIN_API bool NPAPI_Init(mathImpFn_t *mathfn, noePluginFn_t *noepfn)
{
	g_mfn = mathfn;
	g_nfn = noepfn;

	int apiVer = g_nfn->NPAPI_GetAPIVersion();
	if (apiVer < NOESIS_PLUGINAPI_VERSION)
	{
		if (apiVer >= 36)
		{
			g_nfn->NPAPI_MessagePrompt(L"The triangle picker plugin requires a newer version of Noesis than you are currently running!");
		}
		return false;
	}

	int th = g_nfn->NPAPI_RegisterTool("Triangle picker", Visualizer_Invoke, NULL);
	g_nfn->NPAPI_SetToolHelpText(th, "Toggle triangle picker");

	memset(&g_pickMdl, 0, sizeof(pickerMdl_t));
	g_vh = g_nfn->NPAPI_RegisterVisualizer();
	g_nfn->NPAPI_Visualizer_SetPreviewLoaded(g_vh, OnModelLoaded);
	g_nfn->NPAPI_Visualizer_SetPreviewClose(g_vh, OnModelClose);
	g_nfn->NPAPI_Visualizer_SetPreviewReset(g_vh, OnModelReset);

	return true;
}

//called by Noesis before the plugin is freed
NPLUGIN_API void NPAPI_Shutdown(void)
{
}

NPLUGIN_API int NPAPI_GetPluginVer(void)
{
	return NOESIS_PLUGIN_VERSION;
}

NPLUGIN_API bool NPAPI_GetPluginInfo(noePluginInfo_t *infOut)
{
	strcpy_s(infOut->pluginName, 64, "example_visualize02");
	strcpy_s(infOut->pluginDesc, 512, "Visualizer Example 02, by Dick.");
	return true;
}

BOOL APIENTRY DllMain( HMODULE hModule,
                       DWORD  ul_reason_for_call,
                       LPVOID lpReserved
					 )
{
    return TRUE;
}

#ifdef _MANAGED
#pragma managed(pop)
#endif

