# **Comprehensive Capability Map and Engineering Framework for Automated Presentation Toolchains**

The development of a modular Claude Skill library for professional presentation generation represents a significant architectural challenge, requiring the orchestration of disparate technologies including Open XML manipulation, computer vision-based image post-processing, and declarative diagramming. Within the constraints of a sandboxed Linux container devoid of persistent GPU acceleration, the engineering strategy must prioritize efficiency, portability, and long-term maintainability. This report provides an exhaustive analysis of the community-driven Model Context Protocol (MCP) ecosystem, open-source image manipulation libraries, and presentation frameworks to define a robust toolchain architecture.

## **Executive Summary**

The transition from static template-filling to dynamic, AI-augmented presentation engineering necessitates a multi-layered toolchain. This research identifies three primary layers: the standardized interaction layer (MCP), the non-model processing layer (core imaging libraries), and the specialized presentation layer (Open XML and Markdown frameworks).  
The community has already established significant precedents in the MCP registry, particularly with the Office-PowerPoint-MCP-Server, which offers a comprehensive suite of 34 tools for direct PPTX manipulation.1 However, significant capability gaps remain in cross-platform asset management and layout-aware design intelligence. The non-model layer, dominated by libraries such as rembg and OpenCV, provides the necessary post-processing capabilities to transform raw AI-generated visual content into professional slide assets, provided that inference is optimized for CPU environments using technologies like the ONNX Runtime.2  
The proposed architecture follows a P0-P3 prioritization, centering on a core of python-pptx and rembg (P0), extending into vector iconography and declarative diagramming (P1), and eventually incorporating advanced layout-aware RAG systems and automated design linting (P2-P3). This framework ensures that the resulting presentations are not merely collections of images and text, but cohesive, brand-consistent visual narratives.

## **Part 1: Community Skills, Plugins, and Existing Projects**

The burgeoning Model Context Protocol (MCP) ecosystem serves as the primary gateway for integrating external tools into Claude. By analyzing the current landscape of MCP servers and equivalent patterns in the OpenAI and LangChain ecosystems, a clear map of reusable components emerges.

## **1A — Claude Skills and MCP Servers for Image and Presentation Work**

The community has rapidly adopted the MCP standard to provide AI assistants with direct access to local and cloud-based resources. The following catalogue identifies the most relevant servers discovered in repositories such as Smithery.ai, the official Anthropic registry, and independent GitHub projects.

| Skill/Server Name | Repository URL | Primary Capabilities | Maintainer | Relevance & Architecture |
| :---- | :---- | :---- | :---- | :---- |
| **Office-PowerPoint-MCP-Server** | GongRzhe/Office-PowerPoint-MCP-Server | 34 tools for full PPTX manipulation, template support, chart generation, and text extraction. | GongRzhe | **High.** Built on python-pptx. Ideal for Linux sandboxes. 1 |
| **Image Gen MCP** | lansespirit/image-gen-mcp | Multi-provider image generation (OpenAI, Gemini), resource-based image retrieval, and cost estimation. | lansespirit | **High.** Standardizes image prompt engineering and multi-model access. 5 |
| **ImageSorcery MCP** | sunriseapps/imagesorcery-mcp | Local CV tools: crop, resize, rotate, blur, and object detection using YOLO/CLIP. | sunriseapps | **High.** Provides essential "non-model" post-processing in a Python stack. 6 |
| **ppt-mcp** | ykuwai/ppt-mcp | 153 tools for live PowerPoint control via COM automation, Google Material icons, and typography checks. | ykuwai | **Moderate.** Requires Windows/PowerPoint Desktop. Patterns are transferable. 7 |
| **Visio MCP Server** | GongRzhe/Office-Visio-MCP-Server | Programmatic creation and editing of Visio diagrams via COM. | GongRzhe | **Low.** Platform-locked to Windows. Useful for diagramming logic blueprints. 8 |
| **PDF MCP** | anthropics/pdf (Cookbook) | PDF text/table extraction, merging, and image extraction. | Anthropic | **High.** Critical for ingesting source data for presentations. 9 |
| **SVG Converter** | mcpmarket.com/design-tools | Converts SVG images into favicon formats and other raster outputs. | Community | **Moderate.** Useful for asset pipeline finalization. 10 |

The architectural divide in the presentation category is significant: servers like Office-PowerPoint-MCP-Server utilize the Open XML standard to manipulate files directly, which is highly compatible with the target Linux sandbox.1 Conversely, the ppt-mcp server leverages Windows-specific COM Interop, allowing for real-time visual updates and advanced typography checks but tethering the system to the Windows ecosystem.7 For the Claude Skill library, the file-based python-pptx approach is the mandatory path, though it must incorporate the design-aware logic (e.g., auto-detecting "widow lines" or theme-consistent palettes) demonstrated by its Windows-based counterparts.7

## **1B — OpenAI GPT Plugin Ecosystem (Transferable Patterns)**

The OpenAI ecosystem, through GPTs and custom actions, has established patterns for "Slide Designers" and "Diagram Assistants." Most of these tools function as high-level wrappers for external SaaS APIs like Canva, Gamma, or Lucidchart. The transferable pattern here is the use of a "Schema-First" generation approach. Instead of the AI writing raw code, the plugin provides a simplified JSON schema representing the slide content, which a backend worker then translates into the final presentation format.10 This minimizes the token overhead and reduces the chance of syntax errors in complex Open XML structures.

## **1C — LangChain, LlamaIndex, and AutoGen Toolchains**

The broader agentic framework ecosystem has contributed sophisticated workflow orchestration patterns. LangChain's "Tools" and "Multi-Agent" patterns (e.g., LangGraph) enable the separation of concerns between a "Content Architect" (who outlines the presentation) and a "Visual Designer" (who selects images and icons).12  
LlamaIndex provides "Data Connectors" that are superior for RAG-based presentation workflows, where slide content must be derived from complex internal documentation.13 A notable emerging pattern is the "Visual Agent," which uses Multimodal Large Language Models (MLLMs) to inspect a draft slide (rendered as an image) and provide feedback on layout consistency—effectively a "Human-in-the-loop" quality check performed by another AI instance.14

## **Part 2: Open-Source Image Manipulation Libraries**

The "non-model" layer is responsible for the heavy lifting of making AI-generated images fit for a professional presentation. This involves cleaning, scaling, and compositing assets into a coherent theme.

## **Category A: Core Image Processing and Manipulation**

#### **A1 — General-Purpose Image Libraries**

Pillow (PIL) remains the fundamental library for basic operations such as opening, cropping, and simple filtering within a Python environment.15 For more advanced computer vision tasks, OpenCV is the industry standard, providing the necessary hooks for complex drawing operations and spatial transformations.6 In a Linux sandbox, OpenCV typically requires system-level libraries like libgl1-mesa-glx to function correctly.6

#### **A2 — Background Removal and Segmentation**

The rembg library is the most robust open-source choice for background removal, supporting a variety of models such as u2net, isnet-general-use, and the highly efficient silueta (43MB), which is optimized for quick inference on CPUs.2 rembg utilizes the ONNX Runtime, allowing it to leverage multiple CPU threads effectively.2 The Segment Anything Model (SAM) from Meta provides more granular control but carries a higher computational cost, making it better suited for targeted editing rather than batch background removal.2

#### **A3 — Image Compositing and Layer Management**

For complex compositing—such as placing a transparent subject over a branded background with drop shadows—pycairo and skia-python offer professional-grade rendering. These libraries allow for sub-pixel anti-aliasing and sophisticated alpha-channel blending that surpasses the basic capabilities of Pillow.14

#### **A4 — Color Manipulation and Palette Tools**

Maintaining brand consistency requires programmatic color extraction and adjustment. colorthief can extract a dominant palette from a brand asset (like a logo), which can then be used to recolor generated icons or diagrams.7 colour-science provides a more rigorous mathematical framework for color space conversions, ensuring that images rendered for digital screens maintain fidelity across different display types.

#### **A5 — Image Upscaling and Enhancement**

In a CPU-only sandbox, traditional GAN-based upscalers like Real-ESRGAN can be prohibitively slow for 1024x1024 images.20 The engineering team should focus on lightweight transformer-based models like SwinIR-lite or specialized sharpening filters in OpenCV that enhance perceived quality without the overhead of massive neural networks.20

## **Category B: Vector Graphics, Icons, and Diagrams**

#### **B1 — SVG Generation and Manipulation**

SVGs are essential for scalable presentation assets. CairoSVG is the standard tool for converting SVG code into high-DPI raster images for insertion into PowerPoint.22 svgwrite allows for the programmatic generation of vector assets from scratch, which is particularly useful for creating simple charts or branded separators that are too specific for generic icon libraries.

#### **B2 — Icon Libraries and Asset Sources**

The transition from bitmap icons to SVGs is critical. Lucide provides over 1,000 consistent, beautifully designed icons with a highly active community (daily updates).23 Its architectural predecessor, Feather Icons, is considered abandoned, making Lucide the strategic choice for maintenance-conscious architects.24 Iconify offers a unified API to access thousands of icons from diverse sets (Material, Font Awesome, Carbon), which can be wrapped into a Claude Skill for keyword-based icon search and insertion.25

#### **B3 — Programmatic Diagram Generation**

Diagramming is the most efficient way to communicate process and structure on a slide. The toolchain should support:

* **Mermaid:** Best for flowcharts and sequence diagrams. It is highly optimized and widely understood by LLMs.27  
* **D2:** A newer declarative language that produces more "presentation-ready" visuals with better default layouts than Graphviz.27  
* **Graphviz (DOT):** Unrivaled for massive, complex network graphs, though the aesthetic is purely functional.29

#### **B4 — Chart and Data Visualization as Images**

For data-heavy slides, Matplotlib and Seaborn are the standard Python choices.15 To make these charts presentation-ready, the AI must be instructed to use specific styling parameters (e.g., removing background grids, increasing font sizes for legibility from a distance, and using the extracted brand palette).15

## **Category C: Typography and Text Rendering**

Professional typography is often the differentiator between amateur and corporate presentations. While python-pptx handles basic text placement, advanced rendering requires more sophisticated tools.

#### **C1 — Text-on-Image Rendering**

When text must be burned into an image (e.g., for a title slide with a background photo), Pango (via pycairo) provides world-class text layout, including support for complex scripts and ligatures. html2image can also be used to leverage the CSS layout engine of a headless browser to render highly stylized text elements as images.31

#### **C2 — Font Management and Access**

The sandboxed container should be pre-loaded with high-quality, open-source font families (e.g., Inter, Montserrat, Playfair Display). The toolchain must have a registry mapping these fonts to the styles defined in the PowerPoint template to ensure consistency between the Open XML text and any text rendered into raster assets.

## **Category D: Presentation-Specific Tools and Frameworks**

#### **D1 — PPTX Generation Ecosystems**

python-pptx is the uncontested core engine for local PPTX creation, but it has notable limitations, such as the inability to easily copy slides between presentations or change certain link colors.32 To augment this, the team should look at pptx-template, which allows for a "Mail Merge" style approach where a source presentation acts as a template with placeholders.33 Marp and Pandoc provide alternative paths by converting Markdown directly to PPTX, which can be faster for text-heavy drafts but offers less control over fine-grained design elements than the direct Open XML approach.28

#### **D2 — Slide Layout and Design Intelligence**

Research projects like SlideCoder and SlideMaster indicate a shift toward layout-aware generation.35 These systems use RAG to help the AI understand the python-pptx library better and avoid common errors like placing content outside of slide boundaries.35

## **Category E: Image Pipeline Orchestration and Utilities**

#### **E1 — Image Pipeline and Workflow Tools**

Orchestration should be handled by a task-oriented framework. Albumentations and imgaug, while primarily designed for machine learning data augmentation, provide highly efficient pipelines for batch-processing images (e.g., applying a consistent sharpening, brightness, and color-correction filter to all images in a deck).17

#### **E2 — Caching, Storage, and Asset Management**

Since the sandbox is non-persistent, an external caching layer (e.g., Redis) or a structured resource management system (like the URI-based history in the image-gen-mcp) is necessary to allow the AI to reuse assets across multiple slide generation attempts without re-generating or re-downloading them.5

#### **E3 — Image Analysis and Quality Assessment**

To automate QA, the toolchain should use "No-Reference" (NR) metrics:

* **BRISQUE:** Detects technical artifacts like noise and blur.37  
* **NIQE:** Measures "naturalness," which is excellent for detecting surreal or distorted AI-generated artifacts.37  
* **CLIP-IQA:** Uses the CLIP model to score an image based on its alignment with human-perceived quality.37

## **Part 3: Integration Architecture Patterns**

Chaining these tools into a coherent pipeline requires specific architectural patterns to handle the resource constraints of a CPU-only sandbox.

## **3A — Skill Composition Patterns**

The "Sub-Agent" or "Hierarchical Agent" pattern is most effective for presentation work. A "Primary Presentation Agent" decomposes the user's request into discrete tasks, which are then delegated to specialized skills:

1. **Analyst Skill:** Extracts themes and data from input documents (PDF/XLSX).9  
2. **Designer Skill:** Generates image prompts and selects icon keywords from the Lucide registry.23  
3. **Editor Skill:** Post-processes images using rembg and OpenCV to ensure theme consistency.2  
4. **Authoring Skill:** Executes the final python-pptx commands to build the deck.1

This modularity allows for the "plug-and-play" replacement of components as better libraries or models emerge.

## **3B — Performance and Resource Patterns (CPU Focus)**

To maintain acceptable latency in a CPU-bound environment, several engineering tactics are recommended:

* **ONNX Threading:** Set OMP\_NUM\_THREADS to match the available cores for ONNX-based tools like rembg.2  
* **Session Persistence:** Use new\_session() patterns in Python libraries to avoid the overhead of re-loading models for every image in a deck.2  
* **Downsampling for Analysis:** When using vision models to "inspect" a slide, downsample the image to the smallest possible resolution that retains semantic information (e.g., 512x512).15  
* **Asynchronous Generation:** Trigger image generation and diagram rendering in parallel while the main agent is drafting the slide text to minimize total wall-clock time.5

## **3C — Quality Assurance Patterns**

Automated QA should be implemented as a "Visual Linting" step. This includes:

* **Text Fit Validation:** Check if text overflows its container—a common failure in programmatic generation.1  
* **Contrast Checking:** Ensure that extracted brand colors provide enough contrast for readability on both light and dark backgrounds.  
* **Asset Alignment:** Use OpenCV to detect the center of gravity of objects in generated images to ensure they are cropped and positioned aesthetically on the slide.6

## **Required Research Deliverables**

## **Tool Evaluation Matrix (The Architect's Selection)**

| Tool Category | Recommended Tool | License | Stack | CPU Performance |
| :---- | :---- | :---- | :---- | :---- |
| **PPTX Engine** | python-pptx | MIT | Python | High |
| **BG Removal** | rembg (Silueta model) | MIT | Python/ONNX | Moderate |
| **Core CV** | OpenCV | Apache 2.0 | C++/Python | High |
| **Icon Set** | Lucide | ISC | SVG | Very High |
| **Diagrams** | Mermaid | MIT | Node.js | High |
| **Quality Assessment** | BRISQUE (via pyiqa) | MIT | Python | Moderate |
| **Orchestration** | FastMCP | MIT | Python | Very High |

## **Capability Gap Analysis**

Despite the richness of the ecosystem, three critical gaps exist that the team must address through custom engineering:

1. **Semantic Layout Mapping:** There is no open-source tool that can reliably map a raw outline (e.g., "Intro, Problem, Solution, Team") to the complex Master Slide layouts of a random corporate template.  
2. **SmartArt Equivalents:** Programmatic creation of dynamic SmartArt (which users can edit later) is essentially impossible with existing open-source libraries, forcing the use of static grouped shapes.  
3. **Cross-Library Theme Sync:** Syncing the "Accent 1" color across a PowerPoint shape, a Mermaid diagram, and a Matplotlib chart requires a custom "Theme Manager" skill that acts as a single source of truth for the entire pipeline.

## **Recommended Skill Library Architecture (P0-P3 Roadmap)**

* **P0 (Core Infrastructure):** Stabilize the python-pptx and rembg skills. Implement a basic template-based generation flow that can place text and images into placeholders.1  
* **P1 (Visual Enrichment):** Integrate Lucide icon search and Mermaid diagram rendering. Build a "Color Management" skill to unify palettes across all assets.23  
* **P2 (Intelligence & QA):** Implement the "Text Fit" and "BRISQUE" quality checks. Add "Template Profiling" to automatically discover layouts in a user's uploaded PPTX.33  
* **P3 (Advanced Post-Processing):** Incorporate local upscaling and sharpening for low-quality source images. Develop "Layout-Aware RAG" to improve the AI's design reasoning.20

## **Dependency Health Report**

The selected toolchain is built on stable, highly-maintained foundations. python-pptx and OpenCV are industry standards with a "Bus Factor" that is effectively the entire professional software community. rembg and Lucide represent the high-growth "modern" tier of tools with frequent updates and high community engagement.2 All recommended libraries use permissive licenses (MIT, Apache, ISC), ensuring compatibility with corporate deployment and secondary distribution within the Claude Skill library.

## **Integration Cookbook (The Toolsmith's Blueprint)**

**Scenario: Generating a "Market Overview" Slide**

1. **Extract:** The agent calls the PDF Parser skill to pull market data from an annual report.  
2. **Visualize:** The agent calls the Mermaid skill to create a "Market Evolution" flowchart based on the extracted data.  
3. **Illustrate:** The agent calls Image Gen for a "high-tech city skyline" and then rembg to remove the background, making it a professional overlay.  
4. **Compose:** The PPTX Authoring skill selects the "Two Content" layout from the corporate template, placing the Mermaid diagram on the left and the stylized skyline on the right, ensuring all elements use the brand's primary hex code extracted at the start of the session.  
5. **Validate:** The Quality QA skill checks that the slide title isn't too long and that the diagram is perfectly centered within its half of the slide.

## **Source Registry**

The findings in this report are based on the analysis of the following primary sources:

* **MCP Server Registries:** Official Anthropic registry and Smithery.ai collections.9  
* **Open-Source Repository Documentation:** Detailed READMEs and CONFIG files for rembg, imagesorcery-mcp, python-pptx, and Lucide.1  
* **Academic Benchmarks:** Research on super-resolution (Real-ESRGAN/SwinIR) and image quality assessment (BRISQUE/NIQE).20  
* **Developer Publications:** Community insights on "PowerPoint Mazes" and LLM-to-slide generation frameworks.32

This research confirms that while the individual components for professional presentation automation exist, the "engineering value" lies in the orchestration layer—the Claude Skill library that harmonizes these diverse tools into a single, brand-aware creative engine.

#### **Works cited**

1. GongRzhe/Office-PowerPoint-MCP-Server: A MCP (Model ... \- GitHub, accessed March 28, 2026, [https://github.com/GongRzhe/Office-PowerPoint-MCP-Server](https://github.com/GongRzhe/Office-PowerPoint-MCP-Server)  
2. danielgatis/rembg: Rembg is a tool to remove images ... \- GitHub, accessed March 28, 2026, [https://github.com/danielgatis/rembg](https://github.com/danielgatis/rembg)  
3. Office-PowerPoint-MCP-Server \- An MCP tool based on python-pptx for PPT creation and editing, supporting multi-element operations, accessed March 28, 2026, [https://mcp.aibase.com/server/1917147900750262273](https://mcp.aibase.com/server/1917147900750262273)  
4. Get MCP Servers \- PRO MCP, accessed March 28, 2026, [https://promcp.nabinkhair.com.np/servers](https://promcp.nabinkhair.com.np/servers)  
5. lansespirit/image-gen-mcp: An MCP server that integrates ... \- GitHub, accessed March 28, 2026, [https://github.com/lansespirit/image-gen-mcp](https://github.com/lansespirit/image-gen-mcp)  
6. sunriseapps/imagesorcery-mcp: An MCP server providing ... \- GitHub, accessed March 28, 2026, [https://github.com/sunriseapps/imagesorcery-mcp](https://github.com/sunriseapps/imagesorcery-mcp)  
7. ykuwai/ppt-mcp: The world's best PowerPoint MCP server ... \- GitHub, accessed March 28, 2026, [https://github.com/ykuwai/ppt-mcp](https://github.com/ykuwai/ppt-mcp)  
8. GongRzhe/Office-Visio-MCP-Server \- GitHub, accessed March 28, 2026, [https://github.com/GongRzhe/Office-Visio-MCP-Server](https://github.com/GongRzhe/Office-Visio-MCP-Server)  
9. Skills | Smithery, accessed March 28, 2026, [https://smithery.ai/skills?ns=clientt-ai](https://smithery.ai/skills?ns=clientt-ai)  
10. Design Tools Servidores MCP \- Page 14, accessed March 28, 2026, [https://mcpmarket.com/es/categories/design-tools?page=14](https://mcpmarket.com/es/categories/design-tools?page=14)  
11. HighwayofLife/awesome-chatgpt-plugins \- GitHub, accessed March 28, 2026, [https://github.com/HighwayofLife/awesome-chatgpt-plugins](https://github.com/HighwayofLife/awesome-chatgpt-plugins)  
12. The Creative Revolution: Understanding and Harnessing Generative AI & Agentic AI | by yugal-nandurkar | Medium, accessed March 28, 2026, [https://medium.com/@yugalnandurkar5/the-creative-revolution-understanding-and-harnessing-generative-ai-agentic-ai-d46ea6b37635](https://medium.com/@yugalnandurkar5/the-creative-revolution-understanding-and-harnessing-generative-ai-agentic-ai-d46ea6b37635)  
13. Open Source Frameworks for Building Generative AI Applications \- DEV Community, accessed March 28, 2026, [https://dev.to/aws/open-source-frameworks-for-building-generative-ai-applications-532b](https://dev.to/aws/open-source-frameworks-for-building-generative-ai-applications-532b)  
14. Thinking with Images for Multimodal Reasoning: Foundations, Methods, and Future Frontiers \- arXiv, accessed March 28, 2026, [https://arxiv.org/html/2506.23918v3](https://arxiv.org/html/2506.23918v3)  
15. claude-cookbooks/multimodal/using\_sub\_agents.ipynb at main \- GitHub, accessed March 28, 2026, [https://github.com/anthropics/anthropic-cookbook/blob/main/multimodal/using\_sub\_agents.ipynb](https://github.com/anthropics/anthropic-cookbook/blob/main/multimodal/using_sub_agents.ipynb)  
16. dylanhogg/awesome-python \- GitHub, accessed March 28, 2026, [https://github.com/dylanhogg/awesome-python](https://github.com/dylanhogg/awesome-python)  
17. Power of Computer Vision: Development, Applications, and Challenges \- Rapid Innovation, accessed March 28, 2026, [https://www.rapidinnovation.io/post/computer-vision-cv-development](https://www.rapidinnovation.io/post/computer-vision-cv-development)  
18. 10 Free Scripts and Apps to Easily Auto Remove Image Background (Open-source), accessed March 28, 2026, [https://medevel.com/10-image-background-removal/](https://medevel.com/10-image-background-removal/)  
19. ComfyUI Extensions \- Comfy.ICU, accessed March 28, 2026, [https://comfy.icu/extension/](https://comfy.icu/extension/)  
20. JOINT SUPER-RESOLUTION AND IMAGE RESTORATION FOR PLÉIADES NEO IMAGERY \- Semantic Scholar, accessed March 28, 2026, [https://pdfs.semanticscholar.org/cfb3/add7f54e6efea62354c1102c8de5068b2de3.pdf](https://pdfs.semanticscholar.org/cfb3/add7f54e6efea62354c1102c8de5068b2de3.pdf)  
21. (PDF) JOINT SUPER-RESOLUTION AND IMAGE RESTORATION FOR PLÉIADES NEO IMAGERY \- ResearchGate, accessed March 28, 2026, [https://www.researchgate.net/publication/360958195\_JOINT\_SUPER-RESOLUTION\_AND\_IMAGE\_RESTORATION\_FOR\_PLEIADES\_NEO\_IMAGERY](https://www.researchgate.net/publication/360958195_JOINT_SUPER-RESOLUTION_AND_IMAGE_RESTORATION_FOR_PLEIADES_NEO_IMAGERY)  
22. What are the most useful programming languages for creating SVG or DXF? \- Quora, accessed March 28, 2026, [https://www.quora.com/What-are-the-most-useful-programming-languages-for-creating-SVG-or-DXF](https://www.quora.com/What-are-the-most-useful-programming-languages-for-creating-SVG-or-DXF)  
23. lucide-icons/lucide: Beautiful & consistent icon toolkit made ... \- GitHub, accessed March 28, 2026, [https://github.com/lucide-icons/lucide](https://github.com/lucide-icons/lucide)  
24. Best Open Source Linux Icon Sets 2026 \- SourceForge, accessed March 28, 2026, [https://sourceforge.net/directory/icon-sets/linux/](https://sourceforge.net/directory/icon-sets/linux/)  
25. Best Open Source Icon Sets 2026 \- SourceForge, accessed March 28, 2026, [https://sourceforge.net/directory/icon-sets/](https://sourceforge.net/directory/icon-sets/)  
26. icons free download \- SourceForge, accessed March 28, 2026, [https://sourceforge.net/directory/?q=icons](https://sourceforge.net/directory/?q=icons)  
27. Visualization — list of Rust libraries/crates // Lib.rs, accessed March 28, 2026, [https://lib.rs/visualization](https://lib.rs/visualization)  
28. Claude Code skill for MD → Slides; AI makes Markdown great again\! \- GitHub, accessed March 28, 2026, [https://github.com/zl190/md-slides](https://github.com/zl190/md-slides)  
29. Platforms, Servers, Tools, and Utilities | 3rdstage's Wiki | Fandom, accessed March 28, 2026, [https://3rdstage.fandom.com/wiki/Platforms,\_Servers,\_Tools,\_and\_Utilities](https://3rdstage.fandom.com/wiki/Platforms,_Servers,_Tools,_and_Utilities)  
30. claude-cookbooks/capabilities/retrieval\_augmented\_generation/guide.ipynb at main \- GitHub, accessed March 28, 2026, [https://github.com/anthropics/anthropic-cookbook/blob/main/capabilities/retrieval\_augmented\_generation/guide.ipynb](https://github.com/anthropics/anthropic-cookbook/blob/main/capabilities/retrieval_augmented_generation/guide.ipynb)  
31. pptx-manipulation AI Agent Skill \- Free Download | LLMBase, accessed March 28, 2026, [https://llmbase.ai/skills/claude-office-skills/pdf-converter/quickbooks-automation/ppt-visual/etl-pipeline/pptx-manipulation/](https://llmbase.ai/skills/claude-office-skills/pdf-converter/quickbooks-automation/ppt-visual/etl-pipeline/pptx-manipulation/)  
32. Reverse Engineering PowerPoint's XML to Build a Slide Generator \- Listen Labs, accessed March 28, 2026, [https://listenlabs.ai/blog/ppt-generator](https://listenlabs.ai/blog/ppt-generator)  
33. tristan-mcinnis/pptx-from-layouts-skill: Claude Code skill for ... \- GitHub, accessed March 28, 2026, [https://github.com/tristan-mcinnis/pptx-from-layouts-skill](https://github.com/tristan-mcinnis/pptx-from-layouts-skill)  
34. Office PowerPoint MCP Server — Features, Install & Alternatives | FastMCP, accessed March 28, 2026, [https://fastmcp.me/mcp/details/531/office-powerpoint](https://fastmcp.me/mcp/details/531/office-powerpoint)  
35. SlideCoder: Layout-aware RAG-enhanced Hierarchical Slide Generation from Design \- ACL Anthology, accessed March 28, 2026, [https://aclanthology.org/2025.emnlp-main.458.pdf](https://aclanthology.org/2025.emnlp-main.458.pdf)  
36. Kumar Saurabh Ai Camera App | PDF | Statistical Inference | Automation \- Scribd, accessed March 28, 2026, [https://www.scribd.com/document/948242384/Kumar-Saurabh-Ai-Camera-App](https://www.scribd.com/document/948242384/Kumar-Saurabh-Ai-Camera-App)  
37. Libra is an impage comparison to help us quantify and understand differences in images. \- GitHub, accessed March 28, 2026, [https://github.com/lanl/libra](https://github.com/lanl/libra)  
38. Strategic Frameworks for Multimodal Autograding: A Comprehensive Analysis of Vision-Language Models for Text-to-Image Evaluation | by Jane Huang | Feb, 2026 | Medium, accessed March 28, 2026, [https://medium.com/@shujuanhuang/strategic-frameworks-for-multimodal-autograding-a-comprehensive-analysis-of-vision-language-models-26b6aa2b7db2](https://medium.com/@shujuanhuang/strategic-frameworks-for-multimodal-autograding-a-comprehensive-analysis-of-vision-language-models-26b6aa2b7db2)  
39. Image quality assessment based on metrics using quantum algorithms \- SPIE Digital Library, accessed March 28, 2026, [https://www.spiedigitallibrary.org/conference-proceedings-of-spie/13662/136620S/Image-quality-assessment-based-on-metrics-using-quantum-algorithms/10.1117/12.3072742.full](https://www.spiedigitallibrary.org/conference-proceedings-of-spie/13662/136620S/Image-quality-assessment-based-on-metrics-using-quantum-algorithms/10.1117/12.3072742.full)  
40. modelcontextprotocol/servers: Model Context Protocol Servers \- GitHub, accessed March 28, 2026, [https://github.com/modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)