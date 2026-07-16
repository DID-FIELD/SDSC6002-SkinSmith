# SkinSmith Literature Review

> Status: Phase 1 working document  
> Updated: 2026-07-16  
> Citation database: `references.bib`

## Review purpose

This review must establish the academic basis for SkinSmith's design decisions and
identify a defensible research gap. It is not a list of paper summaries.

For every theme, the final synthesis must answer:

1. What does prior work solve?
2. What limitation remains for deployable game-asset textures?
3. Which SkinSmith design responds to that limitation?

## Search and inclusion protocol

Primary sources are preferred:

- peer-reviewed conference or journal papers;
- official proceedings pages;
- author-hosted or arXiv manuscripts when a proceedings record is unavailable;
- authoritative technical documentation only for deployment-specific facts.

Candidate sources are included when they directly support at least one of:

- text-to-image or diffusion generation;
- controllable or spatially conditioned generation;
- texture synthesis and periodicity;
- UV parameterization and texture atlases;
- 3D-aware or multi-view-consistent texture generation;
- differentiable or render-in-the-loop evaluation;
- perceptual or semantic image evaluation;
- constrained multi-objective optimization;
- iterative Agent refinement;
- human-in-the-loop creative systems;
- responsible generative AI and dataset/model documentation.

## Theme 1 - Text-to-image diffusion foundations

Latent diffusion provides the practical foundation for high-resolution
text-conditioned image synthesis by moving denoising into a learned latent space.
This establishes why SkinSmith can use a swappable diffusion or API image backend
for source-art generation. However, a text-conditioned rectangular image does not
encode the target weapon's fragmented UV geometry or mapped multi-view behavior.

The denoising diffusion formulation introduced a stable generative process based on
learning the reverse of gradual noise corruption [@ho2020ddpm]. Later work improved
sampling efficiency and likelihood behavior [@nichol2021improved]. Latent diffusion
reduced computation by moving the process into a learned latent representation and
enabled flexible text conditioning through cross-attention [@rombach2022latent].
CLIP established a broadly useful joint image-text representation
[@radford2021clip], which also motivates semantic compatibility checks.

SkinSmith response: generation is treated as one stage inside an asset-aware
pipeline rather than as the final output.

## Theme 2 - Controllable and spatially conditioned generation

Methods such as ControlNet demonstrate that text prompts alone offer limited
spatial control and that additional structure can guide composition. This supports
SkinSmith's separation between semantic theme planning, textual art direction,
scope/placement contracts, and final geometry-based mapping.

ControlNet adds spatial conditioning such as edge, depth, segmentation, or pose
maps to a pretrained text-to-image model [@zhang2023controlnet]. Its motivation is
directly relevant: complex layouts are difficult to specify through text alone.

SkinSmith response: it does not train a new control network. It combines structured
planning, optional generation references, and deterministic weapon-space-to-UV
mapping around an existing generator.

## Theme 3 - Texture synthesis and seamless periodicity

Classical example-based texture synthesis grows or assembles new textures from
local neighborhoods and patches [@efros1999texture; @efros2001quilting].
Graph-cut texture synthesis improves patch joining by optimizing the seam between
overlapping source regions [@kwatra2003graphcut]. Periodic-plus-smooth
decomposition addresses discontinuities caused by the implicit periodic extension
of finite images in Fourier analysis [@moisan2011periodic].

These methods support Route A as a legitimate generic texture baseline and support
the selected periodic repair method. They also expose an important distinction:
image-border periodicity only concerns opposite edges of a square. A production
mesh contains internal UV-chart boundaries whose corresponding 3D locations need
not lie on the square border.

SkinSmith response: it reports both a square periodic metric and a mesh-derived
asset-seam metric. Route A remains the tileable baseline; Route B targets coherence
after mapping through the real asset.

## Theme 4 - UV parameterization and texture atlases

Surface parameterization maps a 3D surface or surface charts into a lower-dimensional
domain for texture mapping, necessarily introducing trade-offs in distortion and
chart layout [@floater2005parameterization]. Least-squares conformal maps provide
an influential method for generating low-angle-distortion texture atlases and
explicitly note that chart discontinuities can create artifacts and complicate
large regular patterns [@levy2002lscm]. TextureMontage demonstrates the additional
difficulty of placing multiple images on an arbitrary surface while controlling
distortion and transitions across patch boundaries [@zhou2005texturemontage].

SkinSmith does not propose a new parameterization algorithm. Game deployment
requires preserving the asset's authoritative mesh, UV, material, and export
contract. Its contribution begins after that contract is fixed: the system derives
geometry maps and a true seam graph from the bound asset, composes in a continuous
weapon frame, and bakes the composition into the existing fragmented atlas.

## Theme 5 - 3D-aware and multi-view-consistent texturing

Diffusion priors have been used to optimize 3D representations from rendered views
without requiring a large labelled 3D training set [@poole2022dreamfusion].
Mesh-texturing research more directly addresses the present problem. TEXTure and
Text2Tex progressively paint an existing mesh from multiple depth-conditioned
views [@richardson2023texture; @chen2023text2tex]. TexFusion aggregates denoising
predictions through a shared latent texture representation to improve global
consistency [@cao2023texfusion]. Point-UV Diffusion combines point-space
low-frequency structure with UV-space refinement [@yu2023pointuv]. Paint3D adds
specialized UV refinement and removal of baked illumination for production-oriented
2K texture maps [@zeng2024paint3d]. Synchronized multi-view diffusion explicitly
shares denoised content among overlapping views to reduce asynchronous
inconsistency [@liu2024syncmvd].

This literature confirms that multi-view consistency, UV discontinuity,
incompleteness, and embedded illumination are central 3D texturing problems. It
also narrows SkinSmith's novelty claim. SkinSmith is not the first system to use
diffusion for mesh texturing or multi-view consistency.

SkinSmith's distinct research object is a deployable human-Agent workflow around an
existing game asset: one compact theme is expanded into alternatives, the user
selects an original source together with mapped views, the exact source is baked
through the authoritative asset adapter, hard technical constraints govern
selection, and one bounded correction is accepted or rolled back with complete
evidence logging.

## Theme 6 - Rendering and perceptual evaluation

Rendering connects a 3D representation to image-space observations. Differentiable
rendering research shows how image-space supervision can inform mesh or appearance
parameters [@kato2018renderer; @liu2019softras]. SkinSmith uses a deterministic
software renderer rather than gradient-based optimization, but follows the same
general principle that mapped image evidence is needed to reason about 3D asset
behavior.

Deep feature distances can correlate with human perceptual similarity better than
simple pixel metrics in many settings [@zhang2018lpips]. CLIPScore demonstrates
reference-free image-text compatibility scoring while also documenting domains
where such scores are weaker [@hessel2021clipscore]. These findings support using
perceptual and semantic metrics as complementary signals rather than universal
quality measures.

SkinSmith response: texture statistics, true asset seams, fixed multi-view renders,
and optional semantic/readability evidence are kept separate. Automated scores
recommend and explain; they do not replace the user's artwork selection.

## Theme 7 - Constrained multi-objective selection

Penalty-based aggregation can blur the distinction between feasibility and
preference. Deb's feasibility-oriented constraint handling provides a basis for
preferring feasible solutions before comparing objective quality
[@deb2000constraints]. NSGA-II formalizes non-dominated sorting and elitist
multi-objective selection, including constrained variants [@deb2002nsgaii].

SkinSmith does not implement an evolutionary population search. It adapts the
underlying decision principles to a small, expensive candidate pool:

1. reject candidates that violate hard deployment constraints;
2. identify non-dominated feasible candidates;
3. apply a deterministic objective order;
4. preserve weighted aggregation only as an ablation baseline.

The fixed-candidate edge-width experiment directly tests this design: weighted
ranking can prefer an infeasible candidate, while constraint-first/Pareto selection
returns a valid operating point.

## Theme 8 - Iterative Agents and human-in-the-loop creativity

ReAct interleaves model reasoning and tool actions so that observations can update
the task trajectory [@yao2023react]. Self-Refine and Reflexion show that feedback,
reflection, and memory can improve later attempts without retraining model weights
[@madaan2023selfrefine; @shinn2023reflexion]. These works motivate explicit
observation, diagnosis, action, memory, and checkpoint structures, but they do not
guarantee monotonic improvement.

Human-AI interaction guidelines emphasize communicating capabilities, supporting
correction, and giving users appropriate control when AI behavior is uncertain
[@amershi2019guidelines]. Co-creative-system research treats creativity as a
turn-based collaboration rather than full automation [@guzdial2019cocreative].
PromptChainer shows why complex AI tasks benefit from visible staged chains and
intermediate debugging points [@wu2022promptchainer].

SkinSmith response: the Agent has three explicit human checkpoints, persisted
state, bounded budgets, visible evidence, candidate-local retry, and an exact
rollback rule. It intentionally limits refinement to one round rather than
assuming that open-ended self-refinement is safe.

## Theme 9 - Responsible generative AI

Datasheets and model cards establish the value of documenting provenance, intended
use, evaluation conditions, and limitations [@gebru2021datasheets;
@mitchell2019modelcards]. Broader responsible-AI work warns that scale and fluent
outputs can obscure data, environmental, bias, and accountability risks
[@bender2021parrots].

SkinSmith response:

- model/provider IDs, prompts, seeds, hashes, validation, and decisions are logged;
- API keys are redacted;
- formal evidence is immutable;
- Valve assets and model weights are not redistributed without permission;
- prompts prohibit copied skins, protected characters, brands, logos, and living
  artist imitation;
- the final report will disclose AI assistance and generation backends;
- automatic review remains recommendation-only;
- Steam Workshop publication is outside the project scope.

## Provisional research gap

Existing work separately provides powerful text-to-image generation, spatial
conditioning, texture synthesis, 3D-aware generation, and iterative refinement.
The gap addressed by SkinSmith is a practical integration problem:

> converting a compact user theme into a human-selected source design that is
> deterministically bound to an existing game asset's authoritative UV contract,
> evaluated after real geometry mapping, and refined only within explicit hard
> constraints and rollback rules.

This wording is provisional until all literature themes are verified.

## Comparative positioning

| Method family | Existing mesh | Preserves existing UV | Multi-view consistency | Hard deployment constraints | Explicit human checkpoints | Bounded rollback |
|---|---:|---:|---:|---:|---:|---:|
| Generic text-to-image diffusion | No | No | No | No | Prompt only | No |
| Classical tileable texture synthesis | Not required | No | No | Border periodicity | Optional | No |
| Diffusion mesh-texturing systems | Yes | Varies | Yes | Usually method-specific | Usually prompt/edit control | Usually no |
| SkinSmith | Yes | Yes | Evaluated after mapping | Yes | Three | Yes |

The table is a conceptual comparison, not a claim that every paper in a family has
identical properties. The final report should use a paper-level table for the
closest 3D-texturing methods.

## Closest-work comparison

The following comparison is limited to properties stated in the papers' published
descriptions and method summaries. Blank or "not central" cells do not mean that a
system cannot be extended; they mean the property is not its principal reported
contribution.

| Work | Main texture mechanism | Cross-view strategy | UV treatment | Human workflow | Deployment constraints / rollback |
|---|---|---|---|---|---|
| TEXTure [@richardson2023texture] | Iterative depth-conditioned painting of an existing shape | Paints from successive views | Projects generated view content to the mesh texture | Text-guided generation, editing, and transfer | Not its central contribution |
| Text2Tex [@chen2023text2tex] | Progressive generate-then-refine texture synthesis | View partition and automatic next-view selection | Incrementally updates visible texels | Text prompt controls generation | No explicit hard-gate rollback reported |
| TexFusion [@cao2023texfusion] | Denoising over rendered views with a shared latent texture | Aggregates predictions on one latent texture map | Produces a globally coherent texture representation | Text-conditioned generation | No explicit human checkpoint contract |
| Point-UV Diffusion [@yu2023pointuv] | Point-space coarse color followed by UV diffusion | Global low-frequency condition supports consistency | UV diffusion refines high-frequency texture | Conditional generation | No game-specific export gate |
| Paint3D [@zeng2024paint3d] | Coarse multi-view fusion plus UV inpainting and UVHD refinement | View-conditional generation and fusion | Produces high-resolution lighting-less 2K UV maps | Text or image conditioning | Targets texture completeness and relighting, not Agent rollback |
| Synchronized Multi-View Diffusion [@liu2024syncmvd] | Shares denoised latent content across overlapping views | Explicit synchronization during every denoising step | Blends content through texture-domain overlap | Text-guided synthesis | No three-stage human selection contract |
| SkinSmith | User-selected master artwork, deterministic weapon-space fit, OBJ-driven UV bake | Fixed left/right/top preview and evaluation before formal execution | Preserves the authoritative game-asset UV and measures true asset seams | Theme, direction, and mapped-artwork checkpoints | Hard feasibility gates, Pareto selection, one bounded correction, and rollback |

The defensible difference is therefore not "SkinSmith textures 3D meshes while
prior work does not." Prior work clearly does. SkinSmith instead contributes an
asset-bound, evidence-preserving, human-supervised Agent workflow for converting
compact intent into a deployable game texture under explicit technical constraints.

## Literature-supported method mapping

| SkinSmith design | Supporting literature | Adaptation |
|---|---|---|
| Swappable image generator | DDPM, latent diffusion, CLIP | Treat source generation as one pipeline stage |
| Structured art-direction planning | ControlNet motivation; PromptChainer | Use semantic contracts and staged choices without training a new control model |
| Route A tileable baseline | Non-parametric synthesis, quilting, graph cuts, periodic-plus-smooth | Preserve a generic baseline and square-periodicity ablation |
| Authoritative asset binding | Parameterization survey, LSCM, TextureMontage | Retain existing production UV rather than unwrap automatically |
| Route B weapon-space bake | Text2Tex, TEXTure, TexFusion, Point-UV, Paint3D, SyncMVD | Use a selected master artwork and deterministic asset-specific bake |
| Render-in-the-loop evidence | Neural Mesh Renderer, Soft Rasterizer | Use deterministic fixed-view comparison instead of gradient optimization |
| Semantic/perceptual recommendation | LPIPS, CLIPScore | Keep metrics complementary and non-authoritative |
| Constraint-first/Pareto selection | Deb constraint handling, NSGA-II | Apply feasibility and non-dominance to a small expensive candidate pool |
| Bounded Route C | ReAct, Self-Refine, Reflexion | One measured correction round with a hard rollback gate |
| Three checkpoints | Human-AI guidelines, co-creative framework | Preserve human authority over intent, direction, and mapped artwork |
| Provenance and disclosure | Datasheets, model cards, responsible-AI literature | Log model use, limits, evidence, and rights boundaries |

## Review status

| Theme | Target sources | Verified | Synthesis |
|---|---:|---:|---|
| Diffusion foundations | 4-5 | 4 | Drafted |
| Controllable generation | 2-3 | 1 | Drafted |
| Texture synthesis | 4-5 | 4 | Drafted |
| UV/texture atlases | 3-4 | 3 | Drafted |
| 3D-aware texturing | 6-8 | 7 | Drafted |
| Rendering/evaluation | 4-5 | 4 | Drafted |
| Multi-objective optimization | 2-3 | 2 | Drafted |
| Agents/human-in-the-loop | 5-6 | 6 | Drafted |
| Responsible AI | 3-4 | 3 | Drafted |

Current verified database: 34 primary academic sources.

## Remaining literature tasks

- Re-check the full closest-work papers while drafting the final Related Work
  section and attach page-level notes for any detailed comparative claim.
- Add one or two recent review papers for navigation, without replacing primary
  citations.
- Verify venue/page metadata for every BibTeX entry.
- Decide the final citation style required by the report template.
