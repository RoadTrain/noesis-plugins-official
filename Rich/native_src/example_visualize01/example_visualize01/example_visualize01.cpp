// example_visualize01.cpp : Defines the entry point for the DLL application.
//

#include "stdafx.h"
#include <gl/gl.h>
#include <math.h>

mathImpFn_t *g_mfn = NULL;
noePluginFn_t *g_nfn = NULL;

#ifdef _MANAGED
#pragma managed(push, off)
#endif

static bool g_visualizing = false;
static int g_vh = -1;
static sharedModel_t *g_smdl = NULL;
static int g_smdlIdx = -1;

//shared model should never be loaded when a new model is loaded
static void OnModelLoaded(int vh)
{
	assert(!g_smdl);
}

//free the shared model if one is loaded
static void OnModelClose(int vh)
{
	if (g_smdl)
	{
		noeRAPI_t *rapi = g_nfn->NPAPI_GetPreviewRAPI();
		if (rapi)
		{
			rapi->Noesis_FreeSharedModel(g_smdl);
		}
		g_smdl = NULL;
	}
	g_smdlIdx = -1;
}

//locally load a shared model for the selected model in the preview
static bool PreRender(int vh, void *resv, noeSharedGL_t *ngl)
{
	noeRAPI_t *rapi = g_nfn->NPAPI_GetPreviewRAPI();
	if (!rapi)
	{
		return true;
	}
	int mdlIdx = rapi->Noesis_GetSelectedPreviewModel();
	if (mdlIdx < 0)
	{
		return true;
	}
	if (g_smdlIdx != mdlIdx)
	{
		if (g_smdl)
		{
			rapi->Noesis_FreeSharedModel(g_smdl);
			g_smdl = NULL;
		}
		g_smdlIdx = -1;
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
	}

	if (g_smdl)
	{
		return false;
	}
	return true;
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
	bool didSkin = rapi->Noesis_CopyInternalTransforms(g_smdl);
	//vertex morph anims must be manually handled here if you want to support them in your custom rendering
	float tfac = (float)rapi->Noesis_GetTimeMS() * 0.01f;
	ngl->NGL_BindTexture(NULL);
	for (int i = 0; i < g_smdl->numMeshes; i++)
	{
		sharedMesh_t *mesh = g_smdl->meshes+i;
		if (!mesh->verts || !mesh->normals || !mesh->uvs)
		{
			continue;
		}

		//you can also handle blending, etc. here if desired
		ngl->NGL_Enable(GL_ALPHA_TEST);
		ngl->NGL_AlphaFunc(GL_GREATER, 0.2f);
		if (g_smdl->matData &&
			g_smdl->matData->numMaterials > 0 &&
			g_smdl->matData->numTextures > 0 &&
			mesh->materialIdx >= 0 && mesh->materialIdx < g_smdl->matData->numMaterials)
		{
			noesisMaterial_t *mat = g_smdl->matData->materials+mesh->materialIdx;
			if (mat->texIdx >= 0 && mat->texIdx < g_smdl->matData->numTextures)
			{
				noesisTex_t *tex = g_smdl->matData->textures+mat->texIdx;
				ngl->NGL_BindTexture(tex);
			}
			if (mat->alphaTest)
			{
				ngl->NGL_AlphaFunc(GL_GREATER, mat->alphaTest);
			}
		}
		modelVert_t *verts = (didSkin && mesh->transVerts) ? mesh->transVerts : mesh->verts;
		modelVert_t *normals = (didSkin && mesh->transNormals) ? mesh->transNormals : mesh->normals;
		ngl->NGL_Begin(NGL_PRIM_TRIANGLES);
		for (int j = 0; j < mesh->numTris; j++)
		{
			modelTriFace_t *tri = mesh->tris+j;
			WORD *idx = &tri->a;
			for (int k = 0; k < 3; k++)
			{
				modelVert_t *v = verts+idx[k];
				modelVert_t *nrm = normals+idx[k];
				modelTexCoord_t *uv = mesh->uvs+idx[k];
				ngl->NGL_Color4f(1.0f, (sinf(tfac + nrm->x+nrm->y+nrm->z)+1.0f)*0.5f, 0.0f, 1.0f);
				ngl->NGL_TexCoord2fv(&uv->u);
				ngl->NGL_Vertex3fv(&v->x);
			}
		}
		ngl->NGL_End();
		ngl->NGL_Color4f(1.0f, 1.0f, 1.0f, 1.0f);
		ngl->NGL_Disable(GL_ALPHA_TEST);
	}
	ngl->NGL_BindTexture(NULL);
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
		}
		else
		{
			g_nfn->NPAPI_Visualizer_SetPreRender(g_vh, NULL);
			g_nfn->NPAPI_Visualizer_SetPostRender(g_vh, NULL);
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
			g_nfn->NPAPI_MessagePrompt(L"The Magical Pony Fire plugin requires a newer version of Noesis than you are currently running!");
		}
		return false;
	}

	int th = g_nfn->NPAPI_RegisterTool("Magical Pony Fire", Visualizer_Invoke, NULL);
	g_nfn->NPAPI_SetToolHelpText(th, "Toggle a silly example effect");

	g_vh = g_nfn->NPAPI_RegisterVisualizer();
	g_nfn->NPAPI_Visualizer_SetPreviewLoaded(g_vh, OnModelLoaded);
	g_nfn->NPAPI_Visualizer_SetPreviewClose(g_vh, OnModelClose);

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
	strcpy_s(infOut->pluginName, 64, "example_visualize01");
	strcpy_s(infOut->pluginDesc, 512, "Visualizer Example 01, by Dick.");
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

