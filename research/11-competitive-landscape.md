# Competitive Landscape — AI Presentation Tools

**Research Date:** March 2026
**Methodology:** 60+ web searches and direct page fetches across tool websites, review aggregators, industry analyses, and developer communities.

---

## Executive Summary

The AI presentation tool market in 2026 is crowded, well-funded, and converging on similar SaaS-based feature sets. Gamma leads with 70M+ users and a $2.1B valuation. Beautiful.ai dominates smart layout automation. Canva owns the template ecosystem with 610K+ templates. Meanwhile, developer-oriented tools (Slidev, Marp, Reveal.js) remain niche but passionate communities.

**Jack-Tar Deckhand occupies a unique position that no existing tool fills:** a Claude Code skill suite that generates conference-quality .pptx files from the terminal, with local image generation via Ollama, multi-model image routing, zero SaaS lock-in, and full data privacy. The closest competitors are either SaaS platforms requiring browser context-switching (Gamma, Beautiful.ai) or developer markdown tools that produce web-only output without AI content generation (Slidev, Marp).

The competitive moat is the workflow: developers and technical leads who already live in Claude Code never leave their IDE. No browser tab, no account creation, no subscription management, no data uploaded to third-party servers.

---

## 1. Comprehensive Feature Comparison Matrix

### 1A. AI-Native SaaS Platforms

| Feature | Gamma | Tome | Beautiful.ai | Plus AI | SlidesAI | Canva (Magic Design) |
|:---|:---|:---|:---|:---|:---|:---|
| **Type** | SaaS | SaaS (Sunsetting) | SaaS | SaaS Add-on | SaaS Add-on | SaaS |
| **Pricing (Individual/mo)** | Free / $8 / $15 | Was $16-20/mo | $12/mo (annual) | $10-20/mo (annual) | $8-17/mo | Free / $15/mo (Pro) |
| **Output Format** | Web, PDF, PPTX | Web only (was) | Web, PPTX | Google Slides, PPTX | Google Slides | Web, PPTX, PDF |
| **AI Content Gen** | Yes (Gamma Agent) | Yes (was) | Yes (DesignerBot) | Yes | Yes | Yes (Magic Write) |
| **AI Image Gen** | Yes (GPT-Image-1) | Limited | No (stock library) | Yes (Pro plan) | Yes | Yes (Magic Studio) |
| **Smart Auto-Layout** | Yes | No | Yes (Smart Slides) | No | No | Partial |
| **Template Library** | Workspace Templates | N/A | 300+ Smart Slides | Custom upload (Team) | 150+ | 610,000+ |
| **Real-time Collab** | Yes | Yes (was) | Yes (Team plan) | Via Google/PPTX | Via Google | Yes |
| **API/Programmatic** | Yes (Generate API, Jan 2026) | No | No | No | No | Yes (limited) |
| **Offline Capability** | No | No | No | No | No | Limited (desktop app) |
| **Data Privacy** | Cloud-dependent | Cloud-dependent | SOC 2 (Enterprise) | Google Workspace | Google Workspace | Cloud-dependent |
| **Speaker Notes** | Basic | Basic | Basic | Basic | Basic | Basic |
| **PPTX Quality** | Layout shifts on export | N/A | Native export | Native PPTX renderer | Via Google export | Good |

**Sources:** [Gamma pricing](https://gamma.app/pricing), [Gamma review](https://max-productive.ai/ai-tools/gamma/), [Tome pivot analysis](https://skywork.ai/skypage/en/Tome-AI:-A-2025-Deep-Dive-into-the-AI-Storyteller's-Dramatic-Pivot/1972903305876140032), [Beautiful.ai pricing](https://www.beautiful.ai/pricing), [Plus AI pricing](https://plusai.com/pricing), [SlidesAI pricing](https://www.slidesai.io/pricing), [Canva pricing](https://www.canva.com/pricing/)

### 1B. Collaborative & Pitch-Focused Platforms

| Feature | Pitch | Slidebean | Prezo | MagicSlides |
|:---|:---|:---|:---|:---|
| **Type** | SaaS | SaaS | SaaS | SaaS Add-on |
| **Pricing (Individual/mo)** | Free / $15 / $29 | $7-42/mo (annual) | Free / ~$2+ | Free / $7-29/mo |
| **Output Format** | Web, PPTX import | Web, share links | PDF, PPTX, MP4 | Google Slides |
| **AI Content Gen** | Yes (AI actions) | Yes (AI Pitch Builder) | Yes | Yes |
| **AI Image Gen** | Yes (limited) | No | Yes | No |
| **Smart Auto-Layout** | No | Yes (pitch-focused) | No | No |
| **Template Library** | 100+ expert-made | 100+ investor-vetted | Limited | Multiple categories |
| **Real-time Collab** | Yes (core feature) | No | Yes | Via Google |
| **API/Programmatic** | No | No | No | Yes ($0.50/pres) |
| **Offline Capability** | No | No | No | No |
| **Data Privacy** | Cloud-dependent | Cloud-dependent | Cloud-dependent | Cloud-dependent |
| **Unique Feature** | Pitch Rooms, deal spaces | Investor CRM, scoring | Open Canvas, MP4 export | YouTube/PDF/URL input |

**Sources:** [Pitch.com](https://pitch.com/), [Pitch pricing (G2)](https://www.g2.com/products/pitch-pitch/pricing), [Slidebean pricing](https://slidebean.com/pricing), [Prezo.ai](https://prezo.ai/), [MagicSlides pricing](https://www.magicslides.app/pricing), [MagicSlides API](https://www.magicslides.app/pricing/api)

### 1C. Developer / Markdown-Based Tools

| Feature | Slidev | Marp | Reveal.js | Deckset | iA Presenter |
|:---|:---|:---|:---|:---|:---|
| **Type** | OSS / Local | OSS / Local + CLI | OSS / Web | macOS Native | macOS/iOS Native |
| **Pricing** | Free (MIT) | Free (MIT) | Free (MIT) | $20 one-time (Mac) | $2.50/mo or $25/yr |
| **Output Format** | HTML, PDF, PPTX, PNG | HTML, PDF, PPTX, PNG | HTML, PDF | Keynote-style display | PDF, PPTX |
| **Input Format** | Markdown + Vue | Markdown (CommonMark) | HTML + Markdown | Markdown | Markdown |
| **AI Content Gen** | No | No | No | No | No |
| **AI Image Gen** | No | No | No | No | No |
| **Code Highlighting** | Shiki (100+ langs) | Yes | highlight.js | Yes | No |
| **Live Coding** | Yes (Monaco Editor) | No | No | No | No |
| **Interactive Embeds** | Yes (Vue components) | No | Yes (iframe, JS) | Mermaid.js | No |
| **Version Control** | Yes (text files) | Yes (text files) | Yes (text files) | Yes (text files) | Yes (text files) |
| **Presenter Mode** | Yes + recording | Yes | Yes + speaker notes | Yes | Yes (teleprompter) |
| **Offline Capability** | Yes | Yes | Yes | Yes | Yes |
| **Extensibility** | Vue plugins, themes | CSS themes, plugins | JS plugins, themes | 25+ themes | Limited themes |

**Sources:** [Slidev](https://sli.dev/), [Slidev GitHub](https://github.com/slidevjs/slidev), [Marp](https://marp.app/), [Marp CLI GitHub](https://github.com/marp-team/marp-cli), [Reveal.js](https://revealjs.com/), [Deckset](https://www.deckset.com/), [iA Presenter](https://ia.net/presenter)

### 1D. Jack-Tar Deckhand (This Project)

| Feature | Jack-Tar Deckhand |
|:---|:---|
| **Type** | Claude Code Skills (Local) |
| **Pricing** | Free skills + image API costs (~$1-3/deck) |
| **Output Format** | .pptx (native Open XML) |
| **Input** | Natural language via Claude Code |
| **AI Content Gen** | Yes (Claude — full context window) |
| **AI Image Gen** | Yes (Ollama local + cloud API routing) |
| **Smart Auto-Layout** | Planned (python-pptx rules engine) |
| **Template Library** | Theme system (growing) |
| **Real-time Collab** | No (file-based output) |
| **API/Programmatic** | Yes (skills are composable, scriptable) |
| **Offline Capability** | Partial (Ollama local; cloud images need network) |
| **Data Privacy** | Content stays local (except cloud image API calls) |
| **Speaker Notes** | Yes (conference-aware generation) |
| **Conference Intelligence** | Yes (talk structure, pacing, audience calibration) |
| **QA Automation** | Yes (machine-checkable design rules) |
| **Extensibility** | Full (Claude Code skill composition) |

---

## 2. What They Do That We Can't (Yet)

### 2A. Beautiful.ai's Smart Auto-Layout

Beautiful.ai's Smart Slides are intelligent layouts that realign, resize, and animate content automatically. Design rules are coded into Smart Templates that dynamically adapt to user input — text, images, charts — without manual resize, realign, or restyle. If you add too much text, the layout adjusts; if you include a graphic, elements shift to maintain visual balance. This saves users up to 70% of the time it would take in traditional tools. ([Beautiful.ai Smart Slides](https://www.beautiful.ai/smart-slides), [How Beautiful.ai Works](https://www.beautiful.ai/presentation-software))

**Jack-Tar gap:** We generate static layouts via python-pptx. We don't yet have a content-aware reflow engine that dynamically adjusts spacing, font sizes, and element positions based on content volume.

**Mitigation path:** Implement a post-generation QA pass that detects overflow, orphaned text, and spacing violations, then auto-corrects. This is achievable through python-pptx measurement APIs.

### 2B. Gamma's Web-Native Interactive Format

Every Gamma deck has a shareable URL that renders as an interactive web experience — animations, embedded videos, links, and scroll-based reveals all work in-browser. Cards automatically optimise for various devices. Embeds remain functional, transforming a deck into something closer to a mini-website. ([Gamma review](https://www.sketchbubble.com/blog/gamma-explained-a-comprehensive-deep-dive-into-the-ai-powered-presentation-platform/), [Gamma limitations](https://skywork.ai/blog/how-to-fix-gamma-ai-presentation-limitations-2025-guide/))

**Jack-Tar gap:** We produce .pptx files. No web-native interactive format, no shareable URLs, no embedded web content.

**Mitigation:** This is a deliberate trade-off. PPTX is the universal conference format. When you stand on a stage with a clicker, you need PowerPoint/Keynote compatibility — not a browser. The PPTX limitation is actually our strength for the target user.

### 2C. Canva's Massive Template Library

Canva has 610,000+ templates (350,000 premium), with 25+ AI tools under Magic Studio, and serves the broadest possible user base. ([Canva statistics](https://thesocialshepherd.com/blog/canva-statistics), [Canva Pro templates](https://www.canva.com/pro/free-templates/))

**Jack-Tar gap:** We have a small but growing theme system. We cannot compete on template volume.

**Mitigation:** We compete on intelligence, not inventory. One smart theme that adapts to content type (conference talk, technical review, pitch deck) is worth more than 10,000 static templates to our target user.

### 2D. Tome's Narrative Generation (Historical)

Tome could generate complete narrative presentations from a single sentence. However, Tome sunsetting its slides product (April 30, 2025) is a cautionary tale: their tile-based system was incompatible with business workflows (no PPTX export), and users defected to tools that maintained format compatibility. ([Tome pivot analysis](https://autoppt.com/blog/tome-app-pivot-away-from-presentations/), [Tome sunsetting](https://www.pageon.ai/blog/tome-slides-is-sunsetting-on-april-30th-you-need-the-alternative))

**Jack-Tar advantage:** Tome's failure validates our approach — producing standard .pptx files that work everywhere.

### 2E. Plus AI's Deep Google Workspace Integration

Plus AI works natively inside Google Slides and Docs — no platform switching. It creates native PPTX files using its own Open XML renderer. Enterprise customers get custom templates. ([Plus AI](https://plusai.com/), [Plus AI for Google Slides](https://workspace.google.com/marketplace/app/plus_ai_for_google_slides_and_docs/214277172452))

**Jack-Tar gap:** No Google Workspace integration. No browser-based editing.

**Mitigation:** Our users don't want Google Workspace integration — they want to stay in their terminal. The gap is irrelevant for our persona.

### 2F. Real-Time Collaboration

Gamma, Beautiful.ai (Team plan), Pitch, Canva, and Prezo all offer real-time collaborative editing.

**Jack-Tar gap:** No real-time collaboration. Output is a .pptx file.

**Mitigation:** The .pptx file IS the collaboration artifact. Share it via Git, Google Drive, email, or Slack. For our persona (developers), Git-based collaboration on presentation content (as text) is often preferred anyway.

### 2G. Template Marketplace / Ecosystem

Beautiful.ai has 300+ Smart Slides, Slidebean has 100+ investor-vetted templates, Canva has its massive library.

**Jack-Tar gap:** No marketplace.

**Mitigation:** Skills are composable. Community themes can be shared as Claude Code skill configurations. The "marketplace" is GitHub.

---

## 3. What They Miss That We Can Nail

### 3A. Full Claude Code Integration

**No competitor offers this.** The AI assistant IS the presentation tool. Users describe what they want in natural language within their existing development workflow. No browser tab, no context switching, no learning a new interface. The full Claude context window (up to 1M tokens) means the AI can reference your entire codebase, documentation, or research when generating slides.

### 3B. Local Image Generation (Ollama)

As of January 2026, Ollama supports experimental image generation with FLUX.2 Klein and Z-Image-Turbo on macOS. ([Ollama image generation](https://gigazine.net/gsc_news/en/20260123-ollama-ai-image-generation/)) OllamaDiffuser extends this to 40+ models. ([OllamaDiffuser](https://www.ollamadiffuser.com/))

**No competitor offers zero-cost local image generation for presentations.** Every SaaS tool either charges for image generation or requires cloud processing. Jack-Tar can generate draft visuals entirely on the user's machine at zero marginal cost.

### 3C. Multi-Model Image Routing

Jack-Tar routes image generation requests to the optimal model per asset type: Ollama for quick drafts, FLUX for high-quality hero images, DALL-E 3 for photorealistic scenes, Recraft for icons and diagrams. No competitor offers this kind of intelligent routing.

### 3D. Conference-Specific Intelligence

No AI presentation tool is designed specifically for conference talks. They all optimise for "business presentations" or "pitch decks." Jack-Tar can embed conference-specific intelligence:
- Talk structure templates (lightning talk, 30-min session, keynote)
- Pacing guidelines (slides per minute, content density rules)
- Speaker notes calibrated to talk duration
- Audience-appropriate technical depth

### 3E. No SaaS Lock-In

Output is .pptx — fully portable, editable in PowerPoint, Keynote, Google Slides, and LibreOffice Impress. No proprietary format, no vendor lock-in, no "export limitations" based on plan tier.

Gamma charges for watermark-free exports. Beautiful.ai gates PPTX export behind paid plans. Canva limits Magic Design to 10 uses for free users. **Jack-Tar has no such restrictions.**

### 3F. Data Privacy

22% of files uploaded to GenAI SaaS tools contain sensitive information, including source code and proprietary data. IBM's 2025 breach report found one in five organisations experienced breaches through "shadow AI" usage. ([AI data privacy statistics](https://www.protecto.ai/blog/ai-data-privacy-statistics-trends/), [GenAI data exposure](https://www.helpnetsecurity.com/2025/12/24/genai-data-exposure/), [Enterprise AI security](https://www.appsmith.com/blog/ai-data-security))

**Jack-Tar keeps presentation content on the user's machine.** The only external calls are to cloud image generation APIs (when selected over Ollama), and those send only image prompts, not presentation content.

### 3G. Programmability and Composability

Skills can be extended, customised, and composed. A user can create a skill that generates a specific type of presentation for their team's weekly review, pulling data from their monitoring dashboards, and run it with a single command.

### 3H. QA Automation

Machine-checkable design quality rules: font consistency, colour palette compliance, minimum font sizes, text overflow detection, image resolution validation. No SaaS competitor offers automated design QA at this level.

### 3I. Cost Control

Per-image routing means users pay only for cloud images they actually need. Ollama-generated drafts are free. A typical deck with 5-10 cloud-generated images costs $1-3 total. No monthly subscription required.

---

## 4. Pricing Comparison

### 4A. Monthly Cost Comparison (Individual User)

| Tool | Free Tier | Paid (Monthly) | Paid (Annual/mo) | Notes |
|:---|:---|:---|:---|:---|
| **Gamma** | 400 AI credits | $10/mo | $8/mo (Plus), $15/mo (Pro) | No watermark on Plus+ |
| **Tome** | N/A (Sunset) | Was $20/mo | Was $16/mo | Sunsetting April 2025 |
| **Beautiful.ai** | 14-day trial | $45 one-time | $12/mo (Pro annual) | Smart Slides, PPTX export |
| **Plus AI** | 7-day trial | $15-25/mo | $10-20/mo | Google Slides + PPTX |
| **SlidesAI** | 1 pres/mo | ~$10-20/mo | ~$8-17/mo | 2,500-12,000 char limits |
| **Canva** | 10 Magic uses | $15/mo (Pro) | $10/mo (annual) | 610K+ templates |
| **Pitch** | Unlimited free | $15-29/mo | Varies | Collab-focused |
| **Slidebean** | Limited | $12/mo | $7/mo (Starter) | Pitch deck focused |
| **Prezo** | Basic free | From ~$2/mo | Varies | Multi-format output |
| **MagicSlides** | 3 pres/mo | $12-29/mo | ~$7-23/mo | API: $0.50/pres |
| **Slidev** | Unlimited | Free (MIT) | Free | Developer-only |
| **Marp** | Unlimited | Free (MIT) | Free | CLI + VS Code |
| **Reveal.js** | Unlimited | Free (MIT) | Free | Web-based |
| **Deckset** | N/A | N/A | $20 one-time (Mac) | macOS only |
| **iA Presenter** | N/A | $2.50/mo | $25/yr | Writing-focused |
| **Jack-Tar** | Unlimited | Free (skills) | ~$1-3/deck (images) | Pay-per-use images only |

### 4B. Annual Cost Comparison (Power User: 50 decks/year)

| Tool | Annual Cost | Cost/Deck |
|:---|:---|:---|
| **Gamma Pro** | $180/yr | $3.60 |
| **Beautiful.ai Pro** | $144/yr | $2.88 |
| **Plus AI Pro** | $240/yr | $4.80 |
| **Canva Pro** | $120/yr | $2.40 |
| **Slidebean Starter** | $84/yr | $1.68 |
| **Slidev / Marp / Reveal.js** | $0 | $0 (no AI) |
| **Jack-Tar (all cloud images)** | ~$75-150/yr | ~$1.50-3.00 |
| **Jack-Tar (Ollama + selective cloud)** | ~$25-75/yr | ~$0.50-1.50 |

### 4C. Jack-Tar Cost Model Detail

- **Skills:** Free (open source)
- **Claude Code:** User's existing Anthropic subscription
- **Ollama images:** Free (local compute)
- **Cloud image API calls (when used):**
  - DALL-E 3: ~$0.04-0.12/image (depending on resolution)
  - FLUX Pro: ~$0.05-0.06/image
  - Recraft: ~$0.04/image
- **Typical deck (15 slides, 8 images):**
  - All Ollama: $0
  - Mix (3 cloud hero + 5 Ollama): ~$0.30-0.50
  - All cloud (high quality): ~$1.00-2.00

**When is Jack-Tar cheaper?** Almost always for individual users who already have Claude Code. The break-even point vs. Gamma Pro ($180/yr) is approximately 90-120 decks per year when using only cloud images — and significantly fewer when mixing local and cloud generation.

**When is Jack-Tar more expensive?** If a user needs a single deck and doesn't already use Claude Code, subscribing to Gamma or Canva would be faster and cheaper.

---

## 5. Target User Persona for Jack-Tar

### 5A. Primary Persona: The Developer-Presenter

**Who they are:**
- Software engineers, technical leads, architects, DevRel professionals
- Already use Claude Code daily for development work
- Give conference talks, internal tech reviews, architecture presentations
- Comfortable with terminal workflows and CLI tools
- Value programmability, reproducibility, and version control

**Why they want presentations in their terminal:**
- Zero context switching — stay in the same environment where they write code
- Programmable — can script deck generation, automate recurring presentations
- Version controllable — presentation source is text, diffs are meaningful
- Private — sensitive architectural diagrams and code don't leave their machine
- Composable — integrate with their existing automation pipelines

**What presentations they make:**
- Conference talks (30-min sessions, lightning talks, keynotes)
- Internal technical reviews and architecture walkthroughs
- Client-facing technical presentations
- Sprint demos and progress reports
- Pitch decks for technical products

### 5B. Secondary Persona: The Startup Technical Founder

**Who they are:**
- Technical founders who code but also pitch
- Need investor decks, customer presentations, board updates
- Already paying for Claude Code Pro
- Want to minimise SaaS sprawl

### 5C. Anti-Persona: Who Is NOT Our User

- **Non-technical users** who prefer visual drag-and-drop editors
- **Marketing teams** who need brand-heavy templates and real-time collaboration
- **Users who need real-time collaborative editing** in the browser
- **One-off users** who need a single deck and have no Claude Code subscription
- **Users who prioritise animations** and web-native interactive content over .pptx

### 5D. Claude Code User Demographics (Context)

Claude Code launched May 2025 and reached $1 billion in annualised revenue by November 2025. By February 2026, $2.5 billion. Stack Overflow's 2025 developer survey found 84% of surveyed developers use AI tools; 51% use AI daily. The proportion of developers actively using Claude ranges from 41% to 68% across studies. ([Claude statistics](https://backlinko.com/claude-users), [Claude revenue](https://www.businessofapps.com/data/claude-statistics/), [Claude AI statistics](https://www.getpanto.ai/blog/claude-ai-statistics))

This is a large, fast-growing addressable market of developers who already have the prerequisite tool installed.

---

## 6. Feature Roadmap Implications

Based on the competitive analysis, Jack-Tar should prioritise features that deepen its unique advantages rather than chase SaaS feature parity.

### P0 — Core Differentiators (Immediate)

1. **Conference talk intelligence** — No competitor does this. Build talk-type templates (lightning, session, keynote) with automatic pacing and speaker note generation.
2. **QA automation** — Machine-checkable design rules that catch font inconsistencies, colour palette violations, text overflow, and image resolution issues before the user ever opens PowerPoint.
3. **Multi-model image routing** — Intelligent selection of Ollama vs. FLUX vs. DALL-E vs. Recraft based on asset type (hero image, icon, diagram, photo).

### P1 — Competitive Parity Where It Matters (Next)

4. **Content-aware layout adjustment** — Inspired by Beautiful.ai's Smart Slides, build a post-generation pass that detects and fixes overflow, orphan text, and spacing issues via python-pptx measurement APIs.
5. **Theme system expansion** — Not 610K templates, but 10-20 high-quality, conference-tested themes that handle all standard talk formats.
6. **Diagram generation** — Mermaid flowcharts, architecture diagrams, and data visualisations rendered as high-resolution SVGs or PNGs inserted into slides.

### P2 — Ecosystem Growth (Later)

7. **Shareable theme/skill repository** — GitHub-based sharing of presentation themes and specialised skills.
8. **Data-driven slides** — Pull metrics from monitoring dashboards, CI pipelines, or CSV files into charts and tables.
9. **Batch generation** — Script generation of recurring presentations (weekly reports, sprint demos) with dynamic data.

### P3 — Strategic Experiments (Future)

10. **Visual QA via multimodal** — Render slides as images and use Claude's vision capabilities to review design quality, catching issues that rule-based QA misses.
11. **Presentation rehearsal assistant** — Use speaker notes and slide content to generate rehearsal prompts and timing guidance.
12. **PPTX template learning** — Import an existing corporate .pptx template and automatically learn its layout rules, colours, fonts, and slide types for future generation.

### What NOT to Build

- **Real-time collaborative editing** — This is a SaaS feature. Our collaboration model is file-based (Git, shared drives).
- **Web-native presentation format** — Tome tried this and failed. PPTX is the universal conference format.
- **Massive template marketplace** — Canva wins this game. We win on intelligence, not inventory.
- **Google Workspace integration** — Our users live in the terminal, not Google Slides.

---

## 7. Key Industry Trends

### 7A. The Tome Cautionary Tale

Tome raised significant funding and reached 25M users, but sunsetting its slides product by April 2025. The failure mode: a proprietary tile-based format that couldn't export to PowerPoint or present in standard formats. Keith Peiris (Tome CEO) acknowledged: "LLMs are good at starting work, but lack the context required to finish it." The lesson: **format compatibility is non-negotiable.** ([Tome pivot](https://autoppt.com/blog/tome-app-pivot-away-from-presentations/), [Keith Peiris on X](https://x.com/keithpeiris/status/1902817105264906655))

### 7B. The Gamma Juggernaut

Gamma is the market leader: 70M+ users, $100M ARR, $2.1B valuation (Series B led by a16z, November 2025). Their Generate API (GA January 2026) enables programmatic creation at scale. Gamma's success validates that AI-generated presentations are a massive market. But their web-native format and PPTX export quality issues leave a gap for tools that produce native .pptx. ([Gamma Series B](https://max-productive.ai/ai-tools/gamma/))

### 7C. AI Presentation Tool Criticisms (Industry-Wide)

MIT Sloan Management Review and multiple 2025 analyses identify systemic weaknesses across all AI presentation tools:
- Generic, safe content that lacks original thinking or strong opinions
- Struggle with storytelling rhythm and narrative tension
- Confident inclusion of outdated stats or vague claims
- Most tools excel at either content OR design, not both
- Few tools built for strict brand compliance
- Risk of eroding human communication skills through over-reliance
([MIT Sloan Review](https://sloanreview.mit.edu/article/what-genai-tools-can-and-cant-do-for-presentations/), [AI presentation tools limitations](https://www.empowersuite.com/en/blog/ai-presentation-tools))

**Jack-Tar advantage:** By being a Claude Code skill, the AI has access to full project context — codebases, documentation, research notes. This enables presentations grounded in real, specific content rather than generic summaries.

### 7D. Data Privacy as a Growing Concern

22% of files uploaded to GenAI tools contain sensitive information. "Shadow AI" breaches add an average of $670K to breach costs. Nearly 70% of enterprises cite the fast-changing GenAI ecosystem as their top security concern. ([Protecto AI statistics](https://www.protecto.ai/blog/ai-data-privacy-statistics-trends/), [IBM breach report](https://www.helpnetsecurity.com/2025/09/08/ai-data-security-risks-report/), [Enterprise AI insider threat](https://cpl.thalesgroup.com/blog/data-security/ai-new-insider-threat-enterprise-security))

**Jack-Tar advantage:** Content stays on the user's machine. For security-conscious organisations, this is a material differentiator.

---

## 8. Positioning Statement

**Jack-Tar Deckhand** is the presentation tool for developers who refuse to leave their terminal.

While SaaS platforms fight over template counts and collaboration features, Jack-Tar delivers what technical presenters actually need: conference-quality .pptx files generated from natural language, with full project context, local image generation, zero SaaS lock-in, and content that never leaves the user's machine.

It's not a product. It's a capability woven into the developer's existing workflow.

---

## Sources

1. [Gamma pricing](https://gamma.app/pricing)
2. [Gamma review 2026](https://max-productive.ai/ai-tools/gamma/)
3. [Gamma AI review (GamsGo)](https://www.gamsgo.com/blog/gamma-app-review)
4. [Gamma limitations guide](https://skywork.ai/blog/how-to-fix-gamma-ai-presentation-limitations-2025-guide/)
5. [Gamma export formats](https://help.gamma.app/en/articles/8022861-what-s-the-easiest-way-to-export-my-gamma)
6. [Gamma deep dive](https://www.sketchbubble.com/blog/gamma-explained-a-comprehensive-deep-dive-into-the-ai-powered-presentation-platform/)
7. [Tome pivot analysis](https://skywork.ai/skypage/en/Tome-AI:-A-2025-Deep-Dive-into-the-AI-Storyteller's-Dramatic-Pivot/1972903305876140032)
8. [Tome sunsetting](https://www.pageon.ai/blog/tome-slides-is-sunsetting-on-april-30th-you-need-the-alternative)
9. [Tome why pivot](https://autoppt.com/blog/tome-app-pivot-away-from-presentations/)
10. [Keith Peiris (Tome CEO) on X](https://x.com/keithpeiris/status/1902817105264906655)
11. [Beautiful.ai pricing](https://www.beautiful.ai/pricing)
12. [Beautiful.ai Smart Slides](https://www.beautiful.ai/smart-slides)
13. [How Beautiful.ai Works](https://www.beautiful.ai/presentation-software)
14. [Beautiful.ai reviews (Siteefy)](https://siteefy.com/tools/beautiful-ai)
15. [Plus AI pricing](https://plusai.com/pricing)
16. [Plus AI Google Workspace](https://workspace.google.com/marketplace/app/plus_ai_for_google_slides_and_docs/214277172452)
17. [Plus AI for PowerPoint](https://marketplace.microsoft.com/en-us/product/office/wa200007130)
18. [SlidesAI pricing](https://www.slidesai.io/pricing)
19. [SlidesAI review (Elegant Themes)](https://www.elegantthemes.com/blog/business/slidesai-review)
20. [Canva pricing](https://www.canva.com/pricing/)
21. [Canva Magic Design](https://www.canva.com/magic-design/)
22. [Canva statistics](https://thesocialshepherd.com/blog/canva-statistics)
23. [Canva Pro templates](https://www.canva.com/pro/free-templates/)
24. [Pitch.com](https://pitch.com/)
25. [Pitch pricing (G2)](https://www.g2.com/products/pitch-pitch/pricing)
26. [Slidebean pricing](https://slidebean.com/pricing)
27. [Slidebean AI features](https://slidebean.com/)
28. [Prezo.ai](https://prezo.ai/)
29. [Prezo review (AI Chief)](https://aichief.com/ai-productivity-tools/prezo-ai/)
30. [MagicSlides pricing](https://www.magicslides.app/pricing)
31. [MagicSlides API pricing](https://www.magicslides.app/pricing/api)
32. [MagicSlides review](https://www.findyourbestai.com/blog/magicslides-review-2025)
33. [Slidev](https://sli.dev/)
34. [Slidev GitHub](https://github.com/slidevjs/slidev)
35. [Slidev guide](https://sli.dev/guide/why)
36. [Marp](https://marp.app/)
37. [Marp GitHub](https://github.com/marp-team/marp)
38. [Marp CLI](https://github.com/marp-team/marp-cli)
39. [Reveal.js](https://revealjs.com/)
40. [Reveal.js GitHub](https://github.com/hakimel/reveal.js/)
41. [Deckset](https://www.deckset.com/)
42. [Deckset App Store](https://apps.apple.com/us/app/deckset-your-notes-to-slides/id6476942011)
43. [iA Presenter](https://ia.net/presenter)
44. [Claude statistics (Backlinko)](https://backlinko.com/claude-users)
45. [Claude AI statistics (GetPanto)](https://www.getpanto.ai/blog/claude-ai-statistics)
46. [Claude revenue (Business of Apps)](https://www.businessofapps.com/data/claude-statistics/)
47. [AI data privacy statistics](https://www.protecto.ai/blog/ai-data-privacy-statistics-trends/)
48. [GenAI data exposure](https://www.helpnetsecurity.com/2025/12/24/genai-data-exposure/)
49. [Enterprise AI security (AppSmith)](https://www.appsmith.com/blog/ai-data-security)
50. [AI insider threat (Thales)](https://cpl.thalesgroup.com/blog/data-security/ai-new-insider-threat-enterprise-security)
51. [MIT Sloan — GenAI for presentations](https://sloanreview.mit.edu/article/what-genai-tools-can-and-cant-do-for-presentations/)
52. [AI presentation tools limitations](https://www.empowersuite.com/en/blog/ai-presentation-tools)
53. [Code-based presentation tools ranked](https://medium.com/demohub-tutorials/10-code-based-presentation-tools-for-developers-ranked-2025-fe764698f132)
54. [Terminal-based presentations (Presenterm)](https://biggo.com/news/202503171144_Terminal-Based-Presentations-Gain-Traction)
55. [Slides terminal tool](https://github.com/maaslalani/slides)
56. [Ollama image generation](https://gigazine.net/gsc_news/en/20260123-ollama-ai-image-generation/)
57. [Ollama image models](https://www.adwaitx.com/ollama-local-image-generation-z-image-flux2/)
58. [OllamaDiffuser](https://www.ollamadiffuser.com/)
59. [AI presentation APIs guide (SlideSpeak)](https://slidespeak.co/guides/top-5-ai-presentation-apis-2025)
60. [Zapier best AI presentation makers 2026](https://zapier.com/blog/best-ai-presentation-maker/)
61. [Best AI presentation makers (Plus AI)](https://plusai.com/blog/best-ai-presentation-makers)
62. [AI presentation makers tested (Lindy)](https://www.lindy.ai/blog/best-ai-presentation-maker)
63. [Slidev vs Marp discussion](https://github.com/slidevjs/slidev/discussions/86)
64. [Markdown presentation tools list](https://gist.github.com/johnloy/27dd124ad40e210e91c70dd1c24ac8c8)
65. [Choosing a slide library (Tony Cabaye)](https://tonai.github.io/blog/posts/slide-libraries/)
