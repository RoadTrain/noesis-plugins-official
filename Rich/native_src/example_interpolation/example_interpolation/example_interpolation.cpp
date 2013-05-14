// example_visualize02.cpp : Defines the entry point for the DLL application.
//

#include "stdafx.h"
#include <gl/gl.h>
#include <math.h>

const char *g_pPluginName = "example_interpolation";
const char *g_pPluginDesc = "Interpolation visualizer, by Dick.";

#ifdef _MANAGED
#pragma managed(push, off)
#endif

typedef enum
{
	INTERPOLATION_CUBIC = 0,
	INTERPOLATION_CATMULLROM,
	INTERPOLATION_HERMITE,
	INTERPOLATION_CUBICBEZIER,
	INTERPOLATION_BEZIER,
	INTERPOLATION_LINEAR,
	NUM_INTERPOLATION_MODES
} interpMode_e;

static const char *g_interpNames[NUM_INTERPOLATION_MODES] =
{
	"Cubic interpolation",
	"Catmull-Rom interpolation",
	"Hermite interpolation",
	"Cubic Bezier interpolation",
	"Bezier curve",
	"Linear interpolation",
};

static long g_showNameTime = 0;
static unsigned long g_lastFrameTime = 0;

static int g_interpolationMode = 0;

static bool g_visualizing = false;
static int g_vh = -1;

static sharedModel_t *g_smdl = NULL;
static int g_smdlIdx = -1;

static bool g_buttonsRegistered = false;

//shared model should never be loaded when a new model is loaded
static void OnModelLoaded(int vh)
{
	assert(!g_smdl);
}

//free the shared model if one is loaded
static void FreeSharedModel(void)
{
	g_showNameTime = 0;
	g_lastFrameTime = 0;
	noeRAPI_t *rapi = g_nfn->NPAPI_GetPreviewRAPI();
	if (g_smdl)
	{
		if (rapi)
		{
			rapi->Noesis_FreeSharedModel(g_smdl);
		}
		g_smdl = NULL;
	}
	g_smdlIdx = -1;
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

//button callback
static void ChangeModeUse(void)
{
	g_interpolationMode = (g_interpolationMode+1)%NUM_INTERPOLATION_MODES;
	g_showNameTime = 4000;
}

//button visibility check
static bool ChangeModeVisible(void *resv)
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
		rapi->Noesis_RegisterUserButton(NULL, NULL, 0, 0, ChangeModeUse, ChangeModeVisible, "Change interpolation mode",
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
	}

	return true;
}

static inline void DrawSplineChar(noeSharedGL_t *ngl, noeRAPI_t *rapi, const noesisSplineSet_t *ss, float x, float y, float scale)
{
	if (ss->numSplines <= 0)
	{
		return;
	}

	ngl->NGL_Begin(NGL_PRIM_LINES);
	const float fStep = 0.1f;
	for (int i = 0; i < ss->numSplines; i++)
	{
		const noesisSpline_t *spline = ss->splines+i;
		for (int j = 0; j < spline->numKnots; j++)
		{
			int rawIndices[4] = { g_mfn->Math_WrapInt(j-1, spline->numKnots), j, g_mfn->Math_WrapInt(j+1, spline->numKnots), g_mfn->Math_WrapInt(j+2, spline->numKnots) };
			const noesisSplineKnot_t *rawKnots[4] = { spline->knots+rawIndices[0], spline->knots+rawIndices[1], spline->knots+rawIndices[2], spline->knots+rawIndices[3] };
			const noesisSplineKnot_t *knot = spline->knots+j;
			const float *lastOut = rapi->Noesis_SplineLastOut(spline, j);
			const float *lastPos = rapi->Noesis_SplineLastPos(spline, j);
			for (float frac = 0.0f; frac < 1.0f; frac += fStep)
			{
				float fracNext = g_mfn->Math_Min2(frac+fStep, 1.0f);
				float pos[3], posNext[3];
				switch (g_interpolationMode)
				{
				case INTERPOLATION_CUBIC:
					{
						pos[0] = g_mfn->Math_CubicLerp(rawKnots[0]->pos[0], rawKnots[1]->pos[0], rawKnots[2]->pos[0], rawKnots[3]->pos[0], frac);
						pos[1] = g_mfn->Math_CubicLerp(rawKnots[0]->pos[1], rawKnots[1]->pos[1], rawKnots[2]->pos[1], rawKnots[3]->pos[1], frac);
						pos[2] = g_mfn->Math_CubicLerp(rawKnots[0]->pos[2], rawKnots[1]->pos[2], rawKnots[2]->pos[2], rawKnots[3]->pos[2], frac);
						posNext[0] = g_mfn->Math_CubicLerp(rawKnots[0]->pos[0], rawKnots[1]->pos[0], rawKnots[2]->pos[0], rawKnots[3]->pos[0], fracNext);
						posNext[1] = g_mfn->Math_CubicLerp(rawKnots[0]->pos[1], rawKnots[1]->pos[1], rawKnots[2]->pos[1], rawKnots[3]->pos[1], fracNext);
						posNext[2] = g_mfn->Math_CubicLerp(rawKnots[0]->pos[2], rawKnots[1]->pos[2], rawKnots[2]->pos[2], rawKnots[3]->pos[2], fracNext);
					}
					break;
				case INTERPOLATION_CATMULLROM:
					{
						pos[0] = g_mfn->Math_CatmullRomLerp(rawKnots[0]->pos[0], rawKnots[1]->pos[0], rawKnots[2]->pos[0], rawKnots[3]->pos[0], frac);
						pos[1] = g_mfn->Math_CatmullRomLerp(rawKnots[0]->pos[1], rawKnots[1]->pos[1], rawKnots[2]->pos[1], rawKnots[3]->pos[1], frac);
						pos[2] = g_mfn->Math_CatmullRomLerp(rawKnots[0]->pos[2], rawKnots[1]->pos[2], rawKnots[2]->pos[2], rawKnots[3]->pos[2], frac);
						posNext[0] = g_mfn->Math_CatmullRomLerp(rawKnots[0]->pos[0], rawKnots[1]->pos[0], rawKnots[2]->pos[0], rawKnots[3]->pos[0], fracNext);
						posNext[1] = g_mfn->Math_CatmullRomLerp(rawKnots[0]->pos[1], rawKnots[1]->pos[1], rawKnots[2]->pos[1], rawKnots[3]->pos[1], fracNext);
						posNext[2] = g_mfn->Math_CatmullRomLerp(rawKnots[0]->pos[2], rawKnots[1]->pos[2], rawKnots[2]->pos[2], rawKnots[3]->pos[2], fracNext);
					}
					break;
				case INTERPOLATION_HERMITE:
					{
						const float tension = sinf((float)rapi->Noesis_GetFrameTime() / 100.0f);
						const float bias = cosf((float)rapi->Noesis_GetFrameTime() / 200.0f);
						pos[0] = g_mfn->Math_HermiteLerp(rawKnots[0]->pos[0], rawKnots[1]->pos[0], rawKnots[2]->pos[0], rawKnots[3]->pos[0], frac, tension, bias);
						pos[1] = g_mfn->Math_HermiteLerp(rawKnots[0]->pos[1], rawKnots[1]->pos[1], rawKnots[2]->pos[1], rawKnots[3]->pos[1], frac, tension, bias);
						pos[2] = g_mfn->Math_HermiteLerp(rawKnots[0]->pos[2], rawKnots[1]->pos[2], rawKnots[2]->pos[2], rawKnots[3]->pos[2], frac, tension, bias);
						posNext[0] = g_mfn->Math_HermiteLerp(rawKnots[0]->pos[0], rawKnots[1]->pos[0], rawKnots[2]->pos[0], rawKnots[3]->pos[0], fracNext, tension, bias);
						posNext[1] = g_mfn->Math_HermiteLerp(rawKnots[0]->pos[1], rawKnots[1]->pos[1], rawKnots[2]->pos[1], rawKnots[3]->pos[1], fracNext, tension, bias);
						posNext[2] = g_mfn->Math_HermiteLerp(rawKnots[0]->pos[2], rawKnots[1]->pos[2], rawKnots[2]->pos[2], rawKnots[3]->pos[2], fracNext, tension, bias);
					}
					break;
				case INTERPOLATION_CUBICBEZIER:
				case INTERPOLATION_BEZIER:
					{
						g_mfn->Math_CubicBezier3D(lastPos, lastOut, knot->in, knot->pos, frac, pos);
						g_mfn->Math_CubicBezier3D(lastPos, lastOut, knot->in, knot->pos, fracNext, posNext);
					}
					break;
				case INTERPOLATION_LINEAR:
				default:
					{
						pos[0] = g_mfn->Math_LinearLerp(lastPos[0], knot->pos[0], frac);
						pos[1] = g_mfn->Math_LinearLerp(lastPos[1], knot->pos[1], frac);
						pos[2] = g_mfn->Math_LinearLerp(lastPos[2], knot->pos[2], frac);
						posNext[0] = g_mfn->Math_LinearLerp(lastPos[0], knot->pos[0], fracNext);
						posNext[1] = g_mfn->Math_LinearLerp(lastPos[1], knot->pos[1], fracNext);
						posNext[2] = g_mfn->Math_LinearLerp(lastPos[2], knot->pos[2], fracNext);
					}
					break;
				}
				ngl->NGL_Vertex3f(pos[0]*scale + x, pos[1]*scale + y, 0.0f);
				ngl->NGL_Vertex3f(posNext[0]*scale + x, posNext[1]*scale + y, 0.0f);
			}
		}
	}
	ngl->NGL_End();
	//draw points for reference
	/*
	ngl->NGL_PointSize(5.0f);
	ngl->NGL_Begin(NGL_PRIM_POINTS);
	for (int i = 0; i < ss->numSplines; i++)
	{
		const noesisSpline_t *spline = ss->splines+i;
		for (int j = 0; j < spline->numKnots; j++)
		{
			float *pos = spline->knots[j].pos;
			ngl->NGL_Vertex3f(pos[0]*scale + x, pos[1]*scale + y, 0.0f);
		}
	}
	ngl->NGL_PointSize(1.0f);
	ngl->NGL_End();
	*/
}

static inline void DrawSplineString(noeSharedGL_t *ngl, noeRAPI_t *rapi, float x, float y, float scale, const char *str)
{
	const float charPad = 5.0f * scale;
	float cx = x;
	float cy = y;
	for (int i = 0; str[i]; i++)
	{
		const noesisSplineSet_t *ss = g_nfn->Noesis_GetCharSplineSet(str[i]);
		if (!ss || !ss->splines)
		{
			continue;
		}

		float cmins[3], cmaxs[3];
		rapi->Noesis_GetSplineSetBounds(ss, cmins, cmaxs);
		//draw from the center on x, but keep vertical offsets
		DrawSplineChar(ngl, rapi, ss, cx + (cmaxs[0]-cmins[0])*scale*0.5f, cy, scale);
		cx += ((cmaxs[0]-cmins[0])+charPad)*scale;
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

	unsigned long curTime = rapi->Noesis_GetFrameTime();
	if (g_lastFrameTime <= 0)
	{
		g_lastFrameTime = curTime;
	}
	unsigned long frameDelta = curTime-g_lastFrameTime;
	g_lastFrameTime = curTime;

	if (g_smdl->numBones < 2)
	{
		return;
	}
	rapi->Noesis_CopyInternalTransforms(g_smdl);

	ngl->NGL_BindTexture(NULL);
	ngl->NGL_Disable(GL_CULL_FACE);
	ngl->NGL_Disable(GL_DEPTH_TEST);
	ngl->NGL_LineWidth(3.0f);
	ngl->NGL_Color4f(1.0f, 1.0f, 1.0f, 1.0f);
	ngl->NGL_Begin(NGL_PRIM_LINES);
	const int startIndex = 0;
	const int endIndex = g_smdl->numBones;
	int range = endIndex-startIndex;
	if (g_interpolationMode == INTERPOLATION_BEZIER)
	{ //form a bezier curve out of all bone positions
		if (range > 50)
		{ //sane cap for bezier
			range = 50;
		}
		float *positions = (float *)_alloca(sizeof(float)*3*range);
		for (int i = 0; i < range; i++)
		{
			int boneIndex = startIndex+i;
			float *pos = positions+i*3;
			modelBone_t *bone = g_smdl->bones+boneIndex;
			if (skinMats && numSkinMats == g_smdl->numBones)
			{
				modelMatrix_t tmp;
				g_mfn->Math_MatrixMultiply(skinMats+boneIndex, &bone->mat, &tmp);
				g_mfn->Math_VecCopy(tmp.o, pos);
			}
			else
			{
				g_mfn->Math_VecCopy(bone->mat.o, pos);
			}
		}
		const float fStep = 0.01f;
		for (float f = 0.0f; f < 1.0f; f += fStep)
		{ //run through the curve and draw points
			float pos[3];
			float posNext[3];
			g_mfn->Math_Bezier3D(positions, range, f, pos);
			g_mfn->Math_Bezier3D(positions, range, g_mfn->Math_Min2(f+fStep, 1.0f), posNext);
			ngl->NGL_Vertex3fv(pos);
			ngl->NGL_Vertex3fv(posNext);
		}
	}
	else
	{ //assorted interpolations
		for (int i = 0; i < range; i++)
		{
			int indices[4] = { startIndex + g_mfn->Math_WrapInt(i-1, range), startIndex + i, startIndex + g_mfn->Math_WrapInt(i+1, range), startIndex + g_mfn->Math_WrapInt(i+2, range) };
			modelBone_t *bones[4] = { g_smdl->bones+indices[0], g_smdl->bones+indices[1], g_smdl->bones+indices[2], g_smdl->bones+indices[3] };
			modelMatrix_t mats[4];
			if (skinMats && numSkinMats == g_smdl->numBones)
			{
				for (int j = 0; j < 4; j++)
				{
					g_mfn->Math_MatrixMultiply(skinMats+indices[j], &bones[j]->mat, &mats[j]);
				}
			}
			else
			{
				for (int j = 0; j < 4; j++)
				{
					mats[j] = bones[j]->mat;
				}
			}

			const float fStep = 0.05f;
			for (float f = 0.0f; f < 1.0f; f += fStep)
			{
				float frac = g_mfn->Math_Min2(f, 1.0f);
				float fracNext = g_mfn->Math_Min2(f+fStep, 1.0f);
				float pos[3];
				float posNext[3];
				switch (g_interpolationMode)
				{
				case INTERPOLATION_CUBIC:
					{
						pos[0] = g_mfn->Math_CubicLerp(mats[0].o[0], mats[1].o[0], mats[2].o[0], mats[3].o[0], frac);
						pos[1] = g_mfn->Math_CubicLerp(mats[0].o[1], mats[1].o[1], mats[2].o[1], mats[3].o[1], frac);
						pos[2] = g_mfn->Math_CubicLerp(mats[0].o[2], mats[1].o[2], mats[2].o[2], mats[3].o[2], frac);
						posNext[0] = g_mfn->Math_CubicLerp(mats[0].o[0], mats[1].o[0], mats[2].o[0], mats[3].o[0], fracNext);
						posNext[1] = g_mfn->Math_CubicLerp(mats[0].o[1], mats[1].o[1], mats[2].o[1], mats[3].o[1], fracNext);
						posNext[2] = g_mfn->Math_CubicLerp(mats[0].o[2], mats[1].o[2], mats[2].o[2], mats[3].o[2], fracNext);
					}
					break;
				case INTERPOLATION_CATMULLROM:
					{
						pos[0] = g_mfn->Math_CatmullRomLerp(mats[0].o[0], mats[1].o[0], mats[2].o[0], mats[3].o[0], frac);
						pos[1] = g_mfn->Math_CatmullRomLerp(mats[0].o[1], mats[1].o[1], mats[2].o[1], mats[3].o[1], frac);
						pos[2] = g_mfn->Math_CatmullRomLerp(mats[0].o[2], mats[1].o[2], mats[2].o[2], mats[3].o[2], frac);
						posNext[0] = g_mfn->Math_CatmullRomLerp(mats[0].o[0], mats[1].o[0], mats[2].o[0], mats[3].o[0], fracNext);
						posNext[1] = g_mfn->Math_CatmullRomLerp(mats[0].o[1], mats[1].o[1], mats[2].o[1], mats[3].o[1], fracNext);
						posNext[2] = g_mfn->Math_CatmullRomLerp(mats[0].o[2], mats[1].o[2], mats[2].o[2], mats[3].o[2], fracNext);
					}
					break;
				case INTERPOLATION_HERMITE:
					{
						const float tension = sinf((float)rapi->Noesis_GetFrameTime() / 500.0f);
						const float bias = cosf((float)rapi->Noesis_GetFrameTime() / 1000.0f);
						pos[0] = g_mfn->Math_HermiteLerp(mats[0].o[0], mats[1].o[0], mats[2].o[0], mats[3].o[0], frac, tension, bias);
						pos[1] = g_mfn->Math_HermiteLerp(mats[0].o[1], mats[1].o[1], mats[2].o[1], mats[3].o[1], frac, tension, bias);
						pos[2] = g_mfn->Math_HermiteLerp(mats[0].o[2], mats[1].o[2], mats[2].o[2], mats[3].o[2], frac, tension, bias);
						posNext[0] = g_mfn->Math_HermiteLerp(mats[0].o[0], mats[1].o[0], mats[2].o[0], mats[3].o[0], fracNext, tension, bias);
						posNext[1] = g_mfn->Math_HermiteLerp(mats[0].o[1], mats[1].o[1], mats[2].o[1], mats[3].o[1], fracNext, tension, bias);
						posNext[2] = g_mfn->Math_HermiteLerp(mats[0].o[2], mats[1].o[2], mats[2].o[2], mats[3].o[2], fracNext, tension, bias);
					}
					break;
				case INTERPOLATION_CUBICBEZIER:
					{
						float d1[3], d2[3];
						for (int j = 0; j < 3; j++)
						{
							d1[j] = mats[1].o[j] + (mats[0].o[j]-mats[1].o[j])*sinf((float)rapi->Noesis_GetFrameTime() / 500.0f)*0.25f;
							d2[j] = mats[2].o[j] + (mats[3].o[j]-mats[2].o[j])*cosf((float)rapi->Noesis_GetFrameTime() / 500.0f)*0.25f;
						}
						g_mfn->Math_CubicBezier3D(mats[1].o, d1, d2, mats[2].o, frac, pos);
						g_mfn->Math_CubicBezier3D(mats[1].o, d1, d2, mats[2].o, fracNext, posNext);
					}
					break;
				case INTERPOLATION_LINEAR:
				default:
					{
						pos[0] = g_mfn->Math_LinearLerp(mats[1].o[0], mats[2].o[0], frac);
						pos[1] = g_mfn->Math_LinearLerp(mats[1].o[1], mats[2].o[1], frac);
						pos[2] = g_mfn->Math_LinearLerp(mats[1].o[2], mats[2].o[2], frac);
						posNext[0] = g_mfn->Math_LinearLerp(mats[1].o[0], mats[2].o[0], fracNext);
						posNext[1] = g_mfn->Math_LinearLerp(mats[1].o[1], mats[2].o[1], fracNext);
						posNext[2] = g_mfn->Math_LinearLerp(mats[1].o[2], mats[2].o[2], fracNext);
					}
					break;
				}

				ngl->NGL_Vertex3fv(pos);
				ngl->NGL_Vertex3fv(posNext);
			}
		}
	}
	ngl->NGL_End();

	ngl->NGL_LineWidth(1.0f);

	if (g_showNameTime > 0)
	{
		ngl->NGL_ResetProjection(true);
		float screenW, screenH;
		ngl->NGL_GetResolution(screenW, screenH);

		const float scale = (4000.0f - (float)g_showNameTime) * 0.0005f;

		ngl->NGL_Enable(GL_BLEND);
		ngl->NGL_BlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
		ngl->NGL_Color4f(1.0f, 1.0f, 0.0f, g_mfn->Math_Min2((float)g_showNameTime / 2000.0f, 1.0f));

		const float scaleExp = scale*scale*scale;
		DrawSplineString(ngl, rapi, 16.0f - 256.0f*scaleExp, screenH-64.0f, 0.5f + scaleExp, g_interpNames[g_interpolationMode]);
		g_showNameTime -= frameDelta;

		ngl->NGL_Disable(GL_BLEND);
		ngl->NGL_Color4f(1.0f, 1.0f, 1.0f, 1.0f);
	}

	ngl->NGL_Enable(GL_DEPTH_TEST);
	ngl->NGL_Enable(GL_CULL_FACE);
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
			FreeSharedModel();
		}
	}
	return 0;
}

//called by Noesis to init the plugin
bool NPAPI_InitLocal(void)
{
	int apiVer = g_nfn->NPAPI_GetAPIVersion();
	if (apiVer < NOESIS_PLUGINAPI_VERSION)
	{
		if (apiVer >= 36)
		{
			g_nfn->NPAPI_MessagePrompt(L"The interpolation visualizer plugin requires a newer version of Noesis than you are currently running!");
		}
		return false;
	}

	int th = g_nfn->NPAPI_RegisterTool("Skeleton interpolator", Visualizer_Invoke, NULL);
	g_nfn->NPAPI_SetToolHelpText(th, "Toggle skeleton interpolator");

	g_vh = g_nfn->NPAPI_RegisterVisualizer();
	g_nfn->NPAPI_Visualizer_SetPreviewLoaded(g_vh, OnModelLoaded);
	g_nfn->NPAPI_Visualizer_SetPreviewClose(g_vh, OnModelClose);
	g_nfn->NPAPI_Visualizer_SetPreviewReset(g_vh, OnModelReset);

	return true;
}

//called by Noesis before the plugin is freed
void NPAPI_ShutdownLocal(void)
{
	//nothing to do here
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

