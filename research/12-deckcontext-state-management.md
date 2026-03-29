# Research 12: DeckContext Serialisation & Pipeline State Management

> Design document for shared state between Jack-Tar Deckhand skills in Claude Code.

**Date:** 2026-03-28
**Status:** Draft
**Scope:** How 7+ skills in the deck-conductor pipeline share, persist, and recover state without a database, server, or persistent process.

---

## 1. The Constraint: Claude Code Skills Are Not a Server

Every design decision here flows from one fact: **Claude Code skills have no persistent process.** Each skill is invoked by Claude Code in sequence within a conversation. Skills can:

- Read and write files on disk.
- Read the conversation context (previous outputs from other skills).
- Execute shell commands (Python, Node, curl, etc.).

Skills **cannot**:

- Keep in-memory state between invocations.
- Listen on a socket or run a daemon.
- Access a database (unless one happens to be running locally, which we do not assume).

This means state management reduces to two mechanisms: **files on disk** and **conversation context**. The design below uses both, with files as the source of truth and conversation context as a convenience cache.

---

## 2. How the Existing generate-presentation Skill Passes State

Before designing something new, it is worth noting how the existing `generate-presentation` skill (`.claude/skills/generate-presentation/SKILL.md`) manages state today:

1. **Plan in conversation context.** Step 1 produces a slide plan (slide number, title, content, layout type, visual asset needed) as structured text in the conversation. This plan is never written to disk -- it lives only in the conversation.

2. **Assets on disk.** Step 3 generates images to `/tmp/presentation-assets/`. Each image gets a predictable path like `slide-N-image.png`.

3. **Build script on disk.** Step 4 writes a Node.js script to `/tmp/presentation-build.js` that references the image paths.

4. **No persistent state file.** There is no JSON state file. If the skill fails midway, there is no checkpoint. The user must re-run the entire skill.

This approach works for a single skill that runs in one shot. It does **not** work for a multi-skill pipeline where 7+ skills need to read each other's outputs. The deck-conductor needs something more structured.

---

## 3. Serialisation Strategy: Option B (Directory of JSON Files) -- Recommended

### Options Evaluated

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **A: Single JSON file** | One `deck-context.json` updated by each skill | Simple mental model; one file to find | Grows large; merge conflicts if two skills ever write simultaneously; every skill must load/parse the entire file including image manifests |
| **B: Directory of JSON files** | Separate files per contract: `talk-brief.json`, `style-guide.json`, `outline.json`, `image-manifest.json`, etc. | Each skill reads only what it needs; smaller files; easier to inspect and debug; natural checkpointing (a file exists = that step completed) | More files to manage; need a convention for the directory path |
| **C: Hybrid** | Small state in conversation, asset manifest on disk | Reduces disk reads for simple data | Token limits make this fragile for large decks; no persistence if conversation resets |

### Recommendation: Option B

**Rationale:**

1. **Skill independence.** The `imagegen-bridge` skill needs the `style-guide.json` and `outline.json` but does not need the `qa-report.json`. With separate files, each skill reads only its dependencies.

2. **Natural checkpointing.** If the pipeline stops after the narrative-architect skill, `outline.json` exists on disk but `image-manifest.json` does not. The conductor can inspect the directory to determine exactly where to resume.

3. **Human debuggability.** A developer can `cat ./tmp/deck/style-guide.json` to see exactly what the stylist produced. With a single monolithic file, they must dig through a large nested structure.

4. **Conversation context as cache, not source of truth.** Skills can echo a summary of their output into the conversation (e.g., "StyleGuide produced: palette is ocean-blue, fonts are Inter/Merriweather"). This helps the conductor make decisions without reading files. But the authoritative data is always the file on disk.

5. **Consistent with CONSTITUTION.md Article 4.6.** The constitution requires using `./tmp/` (project-local, gitignored) rather than `/tmp/` (system temp). This gives us a stable, predictable location.

### Directory Layout

```
./tmp/deck/
├── pipeline-state.json          # Pipeline metadata: which steps ran, timestamps, status
├── talk-brief.json              # User input (frozen after validation)
├── style-guide.json             # Output of slide-stylist
├── outline.json                 # Output of narrative-architect
├── speaker-notes.json           # Output of speaker-notes-writer
├── image-manifest.json          # Output of imagegen-bridge
├── chart-manifest.json          # Output of chart-renderer
├── qa-report.json               # Output of deck-qa
├── images/                      # Generated image files
│   ├── slide-01-hero.png
│   ├── slide-03-diagram.png
│   ├── slide-07-chart.png
│   └── ...
└── output/                      # Final deliverables
    └── presentation.pptx
```

The `./tmp/deck/` prefix is stable across all skill invocations because skills run from the project root. The `./tmp/` directory is gitignored per CONSTITUTION.md.

---

## 4. JSON Schemas

### 4.1 TalkBrief

The user's input, validated and frozen at pipeline start. No skill modifies this after initial creation.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "TalkBrief",
  "description": "User input describing the presentation requirements",
  "type": "object",
  "required": ["topic", "audience", "duration_minutes"],
  "properties": {
    "topic": {
      "type": "string",
      "description": "The subject of the talk",
      "minLength": 3
    },
    "audience": {
      "type": "string",
      "description": "Who will be watching — e.g., 'senior engineering managers at a Fortune 500'"
    },
    "duration_minutes": {
      "type": "integer",
      "description": "Session length in minutes",
      "enum": [5, 10, 15, 20, 30, 45, 60, 90]
    },
    "tone": {
      "type": "string",
      "description": "Presentation tone",
      "enum": ["professional", "conversational", "technical", "inspirational", "provocative", "storytelling"],
      "default": "professional"
    },
    "key_takeaways": {
      "type": "array",
      "description": "The 2-5 things the audience should remember",
      "items": { "type": "string" },
      "minItems": 1,
      "maxItems": 5
    },
    "branding": {
      "type": "object",
      "description": "Optional corporate branding constraints",
      "properties": {
        "company_name": { "type": "string" },
        "logo_path": { "type": "string", "description": "Path to logo file on disk" },
        "primary_color": { "type": "string", "pattern": "^[0-9A-Fa-f]{6}$", "description": "Hex color without # prefix" },
        "secondary_color": { "type": "string", "pattern": "^[0-9A-Fa-f]{6}$" },
        "font_preference": { "type": "string", "description": "Preferred font family name" }
      }
    },
    "preferences": {
      "type": "object",
      "description": "Style and content preferences",
      "properties": {
        "style": {
          "type": "string",
          "enum": ["minimalist", "data-heavy", "image-rich", "diagram-heavy", "corporate", "creative"],
          "default": "image-rich"
        },
        "slide_count_hint": {
          "type": "integer",
          "description": "Approximate desired slide count (the narrative-architect may adjust)",
          "minimum": 3,
          "maximum": 60
        },
        "image_backend": {
          "type": "string",
          "description": "Preferred image generation backend",
          "enum": ["ollama", "dalle3", "flux-replicate", "stable-diffusion", "ideogram"],
          "default": "ollama"
        },
        "resolution": {
          "type": "string",
          "description": "Target resolution",
          "enum": ["1080p", "1440p"],
          "default": "1080p"
        },
        "include_speaker_notes": {
          "type": "boolean",
          "default": true
        },
        "include_charts": {
          "type": "boolean",
          "default": false
        }
      }
    },
    "data_sources": {
      "type": "array",
      "description": "Data for chart slides — inline JSON, CSV file paths, or prose descriptions",
      "items": {
        "type": "object",
        "properties": {
          "label": { "type": "string" },
          "type": { "type": "string", "enum": ["inline_json", "csv_path", "description"] },
          "content": { "type": "string" }
        },
        "required": ["label", "type", "content"]
      }
    }
  }
}
```

### 4.2 PipelineState

Metadata about the pipeline itself. This is the conductor's control file.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "PipelineState",
  "description": "Tracks which pipeline steps have completed, their status, and timing",
  "type": "object",
  "required": ["pipeline_id", "created_at", "steps"],
  "properties": {
    "pipeline_id": {
      "type": "string",
      "description": "Unique identifier for this pipeline run — ISO timestamp or UUID"
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time"
    },
    "talk_brief_hash": {
      "type": "string",
      "description": "SHA-256 of the talk-brief.json contents — detects if input changed"
    },
    "status": {
      "type": "string",
      "enum": ["running", "completed", "failed", "paused"],
      "description": "Overall pipeline status"
    },
    "current_step": {
      "type": "string",
      "description": "The step currently executing or the step that failed"
    },
    "steps": {
      "type": "object",
      "description": "Status of each pipeline step, keyed by step name",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "status": {
            "type": "string",
            "enum": ["pending", "running", "completed", "failed", "skipped"]
          },
          "started_at": { "type": "string", "format": "date-time" },
          "completed_at": { "type": "string", "format": "date-time" },
          "output_file": {
            "type": "string",
            "description": "Path to the output JSON file this step produced"
          },
          "error": {
            "type": "string",
            "description": "Error message if status is 'failed'"
          },
          "retry_count": {
            "type": "integer",
            "default": 0
          },
          "checksum": {
            "type": "string",
            "description": "SHA-256 of the output file — for cache validation"
          }
        },
        "required": ["status"]
      }
    },
    "step_order": {
      "type": "array",
      "description": "Ordered list of step names defining execution sequence",
      "items": { "type": "string" },
      "default": [
        "validate-brief",
        "slide-stylist",
        "narrative-architect",
        "speaker-notes-writer",
        "imagegen-bridge",
        "chart-renderer",
        "deck-assembler",
        "deck-qa"
      ]
    }
  }
}
```

### 4.3 StyleGuide

Produced by `slide-stylist`. Consumed by `imagegen-bridge`, `chart-renderer`, and `deck-assembler`.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "StyleGuide",
  "description": "Visual design system for the deck",
  "type": "object",
  "required": ["palette", "typography", "layout"],
  "properties": {
    "palette": {
      "type": "object",
      "description": "Color palette — all values are 6-character hex WITHOUT # prefix",
      "required": ["primary", "secondary", "accent", "background", "background_alt", "text_primary", "text_muted"],
      "properties": {
        "primary":        { "type": "string", "pattern": "^[0-9A-Fa-f]{6}$" },
        "secondary":      { "type": "string", "pattern": "^[0-9A-Fa-f]{6}$" },
        "accent":         { "type": "string", "pattern": "^[0-9A-Fa-f]{6}$" },
        "background":     { "type": "string", "pattern": "^[0-9A-Fa-f]{6}$", "description": "Light background for content slides" },
        "background_alt": { "type": "string", "pattern": "^[0-9A-Fa-f]{6}$", "description": "Dark background for title/closing/section slides" },
        "text_primary":   { "type": "string", "pattern": "^[0-9A-Fa-f]{6}$" },
        "text_muted":     { "type": "string", "pattern": "^[0-9A-Fa-f]{6}$" },
        "text_on_dark":   { "type": "string", "pattern": "^[0-9A-Fa-f]{6}$", "description": "Text color for dark backgrounds" },
        "chart_series": {
          "type": "array",
          "description": "Ordered colors for chart data series",
          "items": { "type": "string", "pattern": "^[0-9A-Fa-f]{6}$" },
          "minItems": 3,
          "maxItems": 8
        }
      }
    },
    "typography": {
      "type": "object",
      "required": ["heading_font", "body_font"],
      "properties": {
        "heading_font": {
          "type": "string",
          "description": "Font family for headings — must be available on the target system"
        },
        "body_font": {
          "type": "string",
          "description": "Font family for body text"
        },
        "mono_font": {
          "type": "string",
          "description": "Font family for code snippets",
          "default": "Courier New"
        },
        "heading_sizes": {
          "type": "object",
          "description": "Font sizes in points",
          "properties": {
            "title_slide": { "type": "number", "default": 44 },
            "section_divider": { "type": "number", "default": 36 },
            "slide_heading": { "type": "number", "default": 28 },
            "subheading": { "type": "number", "default": 20 }
          }
        },
        "body_size": { "type": "number", "default": 16 },
        "caption_size": { "type": "number", "default": 12 },
        "line_spacing": { "type": "number", "default": 1.4 }
      }
    },
    "layout": {
      "type": "object",
      "description": "Layout rules and templates",
      "properties": {
        "slide_width_inches": { "type": "number", "default": 10 },
        "slide_height_inches": { "type": "number", "default": 5.625 },
        "margin_inches": { "type": "number", "default": 0.5, "description": "Minimum margin from slide edge" },
        "templates": {
          "type": "object",
          "description": "Layout templates keyed by slide type",
          "additionalProperties": {
            "type": "object",
            "properties": {
              "description": { "type": "string" },
              "text_zone": {
                "type": "object",
                "description": "Bounding box for text content in inches from top-left",
                "properties": {
                  "x": { "type": "number" },
                  "y": { "type": "number" },
                  "w": { "type": "number" },
                  "h": { "type": "number" }
                }
              },
              "image_zone": {
                "type": "object",
                "description": "Bounding box for image placement in inches from top-left",
                "properties": {
                  "x": { "type": "number" },
                  "y": { "type": "number" },
                  "w": { "type": "number" },
                  "h": { "type": "number" }
                }
              },
              "background_treatment": {
                "type": "string",
                "enum": ["solid_light", "solid_dark", "image_bleed", "pattern_tile", "gradient"],
                "default": "solid_light"
              }
            }
          }
        }
      }
    },
    "image_style_tokens": {
      "type": "object",
      "description": "Tokens appended to image generation prompts for visual consistency",
      "properties": {
        "mood": { "type": "string", "description": "e.g., 'professional and calm', 'energetic and bold'" },
        "color_direction": { "type": "string", "description": "e.g., 'predominantly deep blue and white tones'" },
        "style_modifiers": {
          "type": "array",
          "description": "Prompt suffixes for consistent image style",
          "items": { "type": "string" }
        }
      }
    }
  }
}
```

### 4.4 SlideOutline

Produced by `narrative-architect`. The backbone of the deck.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SlideOutline",
  "description": "Ordered array of slide definitions forming the deck structure",
  "type": "object",
  "required": ["slides", "narrative_arc", "estimated_duration_minutes"],
  "properties": {
    "narrative_arc": {
      "type": "string",
      "description": "The arc pattern used — e.g., 'situation-complication-resolution', 'hook-body-callback-cta'"
    },
    "estimated_duration_minutes": {
      "type": "number",
      "description": "Estimated total presentation duration based on slide count and density"
    },
    "total_slides": {
      "type": "integer"
    },
    "slides": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["slide_number", "slide_type", "headline"],
        "properties": {
          "slide_number": {
            "type": "integer",
            "minimum": 1
          },
          "slide_type": {
            "type": "string",
            "enum": [
              "title",
              "section_divider",
              "content",
              "two_column",
              "image_feature",
              "data_chart",
              "stat_callout",
              "quote",
              "icon_grid",
              "diagram",
              "closing",
              "blank_visual"
            ]
          },
          "headline": {
            "type": "string",
            "description": "The slide's main headline — short, punchy, conference-appropriate"
          },
          "body_points": {
            "type": "array",
            "description": "Bullet points or key messages for this slide",
            "items": { "type": "string" },
            "maxItems": 5
          },
          "narrative_beat": {
            "type": "string",
            "description": "Where this slide sits in the narrative arc — e.g., 'hook', 'evidence-2', 'callback', 'cta'"
          },
          "visual_direction": {
            "type": "string",
            "description": "Prose description of the visual asset needed — used as input to image generation prompts"
          },
          "visual_type": {
            "type": "string",
            "description": "What kind of visual asset this slide needs",
            "enum": ["hero_image", "diagram", "chart", "icon_set", "pattern_background", "none"]
          },
          "data": {
            "type": "object",
            "description": "Data payload for chart/stat slides",
            "properties": {
              "chart_type": {
                "type": "string",
                "enum": ["bar", "line", "area", "pie", "donut", "scatter", "comparison_table", "timeline", "stat_card"]
              },
              "data_source_label": {
                "type": "string",
                "description": "References a label in TalkBrief.data_sources"
              },
              "inline_data": {
                "type": "object",
                "description": "Inline data if not referencing an external source"
              }
            }
          },
          "layout_template": {
            "type": "string",
            "description": "Which layout template from the StyleGuide to use — e.g., 'two_column_left_image', 'full_bleed_image'"
          },
          "transition_note": {
            "type": "string",
            "description": "How the speaker transitions into this slide from the previous one"
          }
        }
      }
    }
  }
}
```

### 4.5 SpeakerNotes

Produced by `speaker-notes-writer`. Per-slide notes keyed by slide number.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SpeakerNotes",
  "description": "Speaker notes for each slide, keyed by slide number",
  "type": "object",
  "required": ["notes"],
  "properties": {
    "target_pace_wpm": {
      "type": "integer",
      "description": "Target speaking pace in words per minute",
      "default": 130
    },
    "total_estimated_minutes": {
      "type": "number"
    },
    "notes": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["slide_number", "text"],
        "properties": {
          "slide_number": { "type": "integer" },
          "text": {
            "type": "string",
            "description": "The speaker notes text — plain text with timing markers"
          },
          "estimated_seconds": {
            "type": "integer",
            "description": "Estimated speaking duration for this slide"
          },
          "timing_marker": {
            "type": "string",
            "description": "Cumulative time mark — e.g., '~5:30'"
          },
          "cues": {
            "type": "array",
            "description": "Interaction cues for the speaker",
            "items": {
              "type": "object",
              "properties": {
                "type": {
                  "type": "string",
                  "enum": ["transition", "pause", "audience_interaction", "emphasis", "demo", "build_animation"]
                },
                "text": { "type": "string" }
              }
            }
          }
        }
      }
    }
  }
}
```

### 4.6 ImageManifest

Produced by `imagegen-bridge`. Records every generated image and where it goes.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ImageManifest",
  "description": "Registry of all generated image assets with metadata and placement info",
  "type": "object",
  "required": ["images"],
  "properties": {
    "generated_at": {
      "type": "string",
      "format": "date-time"
    },
    "image_backend": {
      "type": "string",
      "description": "Which backend generated these images — e.g., 'ollama/x-z-image-turbo'"
    },
    "images": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["image_id", "slide_number", "file_path", "status"],
        "properties": {
          "image_id": {
            "type": "string",
            "description": "Unique ID — e.g., 'slide-03-hero' or 'slide-07-chart-bg'"
          },
          "slide_number": {
            "type": "integer"
          },
          "file_path": {
            "type": "string",
            "description": "Relative path from project root — e.g., './tmp/deck/images/slide-03-hero.png'"
          },
          "placement_zone": {
            "type": "string",
            "description": "Which zone in the layout template — e.g., 'image_zone', 'background', 'icon_1'"
          },
          "dimensions": {
            "type": "object",
            "properties": {
              "width": { "type": "integer" },
              "height": { "type": "integer" }
            }
          },
          "source_prompt": {
            "type": "string",
            "description": "The exact prompt sent to the image generation model"
          },
          "model_used": {
            "type": "string",
            "description": "Model identifier — e.g., 'x/z-image-turbo'"
          },
          "alt_text": {
            "type": "string",
            "description": "Accessibility alt text for the image"
          },
          "content_hash": {
            "type": "string",
            "description": "SHA-256 hash of the image file bytes — for cache keying and integrity"
          },
          "cache_key": {
            "type": "string",
            "description": "The full cache key used for DiskCache lookup — SHA-256 of prompt+dims+style+model"
          },
          "status": {
            "type": "string",
            "enum": ["generated", "cached", "placeholder", "failed"],
            "description": "Whether the image was freshly generated, served from cache, is a placeholder, or failed"
          },
          "retry_count": {
            "type": "integer",
            "default": 0
          },
          "generation_time_seconds": {
            "type": "number",
            "description": "How long generation took — useful for performance tuning"
          }
        }
      }
    },
    "summary": {
      "type": "object",
      "description": "Aggregate stats for the conductor",
      "properties": {
        "total_images": { "type": "integer" },
        "generated_count": { "type": "integer" },
        "cached_count": { "type": "integer" },
        "placeholder_count": { "type": "integer" },
        "failed_count": { "type": "integer" },
        "total_generation_seconds": { "type": "number" }
      }
    }
  }
}
```

### 4.7 ChartManifest

Produced by `chart-renderer`. Same pattern as ImageManifest but for chart-specific assets.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ChartManifest",
  "description": "Registry of all rendered chart assets",
  "type": "object",
  "required": ["charts"],
  "properties": {
    "charts": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["chart_id", "slide_number", "file_path", "chart_type", "status"],
        "properties": {
          "chart_id": { "type": "string" },
          "slide_number": { "type": "integer" },
          "file_path": { "type": "string" },
          "chart_type": {
            "type": "string",
            "enum": ["bar", "line", "area", "pie", "donut", "scatter", "comparison_table", "timeline", "stat_card"]
          },
          "data_source_label": { "type": "string" },
          "alt_text": { "type": "string" },
          "dimensions": {
            "type": "object",
            "properties": {
              "width": { "type": "integer" },
              "height": { "type": "integer" }
            }
          },
          "content_hash": { "type": "string" },
          "status": {
            "type": "string",
            "enum": ["rendered", "cached", "failed"]
          }
        }
      }
    }
  }
}
```

### 4.8 QAReport

Produced by `deck-qa`. Consumed by the conductor for retry decisions.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "QAReport",
  "description": "Quality assurance findings from deck-qa",
  "type": "object",
  "required": ["findings", "verdict"],
  "properties": {
    "inspected_at": {
      "type": "string",
      "format": "date-time"
    },
    "pptx_path": {
      "type": "string",
      "description": "Path to the .pptx file that was inspected"
    },
    "verdict": {
      "type": "string",
      "enum": ["pass", "pass_with_warnings", "fail"],
      "description": "Overall verdict"
    },
    "summary": {
      "type": "object",
      "properties": {
        "total_slides": { "type": "integer" },
        "errors": { "type": "integer" },
        "warnings": { "type": "integer" },
        "info": { "type": "integer" }
      }
    },
    "findings": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["slide_number", "severity", "category", "description"],
        "properties": {
          "slide_number": { "type": "integer" },
          "severity": {
            "type": "string",
            "enum": ["error", "warning", "info"]
          },
          "category": {
            "type": "string",
            "enum": [
              "overlap",
              "contrast",
              "margin",
              "text_overflow",
              "consistency",
              "image_quality",
              "placeholder_residue",
              "missing_content",
              "accessibility"
            ]
          },
          "description": {
            "type": "string",
            "description": "Human-readable description of the issue"
          },
          "suggested_fix": {
            "type": "string",
            "description": "What the conductor should do — e.g., 'Increase text box width by 0.5 inches'"
          },
          "affected_element": {
            "type": "string",
            "description": "Which element is affected — e.g., 'headline text box', 'hero image'"
          },
          "auto_fixable": {
            "type": "boolean",
            "description": "Whether the conductor can fix this automatically",
            "default": false
          }
        }
      }
    }
  }
}
```

---

## 5. Pipeline Execution Sequence

```
User provides talk description
          │
          ▼
┌─────────────────────┐
│  deck-conductor     │  Parses input, writes talk-brief.json,
│  (orchestrator)     │  creates pipeline-state.json
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  validate-brief     │  Validates TalkBrief schema, resolves
│                     │  defaults, checks branding assets exist
│  Reads:  talk-brief.json
│  Writes: talk-brief.json (with defaults resolved)
│  Updates: pipeline-state.json
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  slide-stylist      │  Derives palette, fonts, layout templates
│                     │  from topic + audience + tone
│  Reads:  talk-brief.json
│  Writes: style-guide.json
│  Updates: pipeline-state.json
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  narrative-architect│  Produces the slide outline with per-slide
│                     │  visual direction and narrative beats
│  Reads:  talk-brief.json, style-guide.json
│  Writes: outline.json
│  Updates: pipeline-state.json
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  speaker-notes-     │  Generates speaker notes for each slide
│  writer             │
│  Reads:  talk-brief.json, outline.json
│  Writes: speaker-notes.json
│  Updates: pipeline-state.json
└────────┬────────────┘
         │
         ├──────────────────────────┐
         ▼                          ▼
┌────────────────┐      ┌────────────────┐
│ imagegen-bridge│      │ chart-renderer │  (parallel if both needed)
│                │      │                │
│ Reads: outline │      │ Reads: outline │
│   style-guide  │      │   style-guide  │
│   talk-brief   │      │   talk-brief   │
│ Writes:        │      │ Writes:        │
│   image-       │      │   chart-       │
│   manifest.json│      │   manifest.json│
│   images/*.png │      │   images/*.png │
└───────┬────────┘      └───────┬────────┘
        │                       │
        └───────────┬───────────┘
                    ▼
┌─────────────────────┐
│  deck-assembler     │  Composes the final .pptx
│                     │
│  Reads:  ALL of the above (outline, style-guide,
│          speaker-notes, image-manifest, chart-manifest)
│  Writes: ./tmp/deck/output/presentation.pptx
│  Updates: pipeline-state.json
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  deck-qa            │  Inspects the .pptx for issues
│                     │
│  Reads:  presentation.pptx, style-guide.json
│  Writes: qa-report.json
│  Updates: pipeline-state.json
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  deck-conductor     │  Reads qa-report.json.
│  (decision point)   │  If verdict=pass: done.
│                     │  If verdict=fail: retry affected skills.
└─────────────────────┘
```

### Skill Dependency Graph

```
talk-brief.json ──► slide-stylist ──► style-guide.json
                │                       │
                │                       ▼
                └──► narrative-architect ──► outline.json
                       │                       │
                       │                       ├──► speaker-notes-writer ──► speaker-notes.json
                       │                       │
                       │                       ├──► imagegen-bridge ──► image-manifest.json + images/
                       │                       │
                       │                       └──► chart-renderer ──► chart-manifest.json + images/
                       │
                       └─────── all outputs ──► deck-assembler ──► presentation.pptx
                                                                       │
                                                                       └──► deck-qa ──► qa-report.json
```

---

## 6. Checkpoint and Resumability

### How It Works

Each skill, upon successful completion, writes its output file and updates `pipeline-state.json`. The conductor checks which steps have `"status": "completed"` before deciding what to run next.

**Resumability algorithm (pseudocode):**

```
function resume_pipeline():
    state = read("./tmp/deck/pipeline-state.json")

    for step in state.step_order:
        step_state = state.steps[step]

        if step_state.status == "completed":
            # Verify output file still exists and hash matches
            if file_exists(step_state.output_file) and
               sha256(step_state.output_file) == step_state.checksum:
                skip(step)  # Already done, output is valid
            else:
                run(step)   # Output corrupted or deleted, re-run

        elif step_state.status == "failed":
            if step_state.retry_count < MAX_RETRIES:
                run(step)   # Retry
            else:
                abort("Step {step} failed {MAX_RETRIES} times")

        else:  # pending, running (interrupted)
            run(step)
```

### Scenario: Image Generation Fails on Slide 15 of 25

This is the critical resumability case. Here is exactly how it works:

1. The `imagegen-bridge` skill processes slides sequentially (or in small batches). As each image is generated, it **appends** to `image-manifest.json`. It does not wait until all images are done to write the file.

2. When slide 15 fails (e.g., Ollama times out), the skill:
   - Records the failure in the manifest: `{ "image_id": "slide-15-hero", "status": "failed", "error": "Ollama timeout after 600s" }`
   - Decides whether to continue with slides 16-25 or stop (configurable: `fail_fast` vs `best_effort` mode).
   - In `best_effort` mode (recommended default): continues generating remaining slides, marks slide 15 as `"placeholder"`, and records a placeholder image path.
   - Updates `pipeline-state.json` with the partial completion.

3. When the conductor sees the image-manifest has failures, it can:
   - **Retry just the failed images.** The conductor re-invokes `imagegen-bridge` with a flag like `--retry-failed-only`. The skill reads `image-manifest.json`, finds entries with `"status": "failed"` or `"status": "placeholder"`, and regenerates only those.
   - **Continue with placeholders.** The `deck-assembler` recognises `"status": "placeholder"` entries and uses a solid-color rectangle with the alt text overlaid, so the deck is still usable.

4. Images 1-14 and 16-25 are **not regenerated**. Their entries in the manifest have `"status": "generated"` and valid `file_path` values. The retry pass skips them.

### What Metadata Is Saved for Each Completed Step

For the pipeline-state, each completed step records:

| Field | Purpose |
|-------|---------|
| `status: "completed"` | The step finished successfully |
| `started_at`, `completed_at` | Timing for performance analysis |
| `output_file` | Path to the output JSON (for the conductor to read) |
| `checksum` | SHA-256 of the output file (detects corruption or manual edits) |
| `retry_count` | How many times this step was attempted |

For the image-manifest specifically, each individual image records its own status, so partial completion is tracked at the per-image level, not just per-step.

---

## 7. Asset Reference Pattern

### Recommendation: Combined Path + Hash

Each image in the manifest uses both a file path and a content hash:

```json
{
  "image_id": "slide-03-hero",
  "slide_number": 3,
  "file_path": "./tmp/deck/images/slide-03-hero.png",
  "content_hash": "sha256:a1b2c3d4e5f6...",
  "cache_key": "sha256:f6e5d4c3b2a1...",
  "placement_zone": "image_zone",
  "status": "generated"
}
```

**Why both:**

- `file_path` is what the `deck-assembler` uses to load the image. It is the operational reference. All paths are relative to the project root (starting with `./`) so they work regardless of the user's home directory.
- `content_hash` is what the caching system uses to verify integrity. If the file exists but the hash does not match, the image was corrupted or manually replaced.
- `cache_key` is a separate hash derived from the generation inputs (prompt + dimensions + style tokens + model version). This is used to check the DiskCache **before** generating: "Have I already generated an image with these exact inputs?"

**How ImageManifest connects to SlideOutline:**

The `slide_number` field is the join key. The outline says slide 3 needs a `hero_image` with `visual_direction: "A vast ocean at dawn..."`. The image-manifest records that `slide-03-hero` was generated for slide 3 and should be placed in the `image_zone` of that slide's layout template. The `deck-assembler` reads both files, matches by slide number, and places the image.

For slides that need multiple images (e.g., an `icon_grid` with 4 icons), the manifest contains multiple entries for the same slide number, differentiated by `image_id` (e.g., `slide-05-icon-1`, `slide-05-icon-2`, etc.) and `placement_zone` (e.g., `icon_1`, `icon_2`, etc.).

---

## 8. Error Recovery Patterns

### 8.1 Fallback Chains

Each skill has a defined fallback chain. The conductor applies these in order:

```
Image Generation Failure:
  1. Retry with same prompt (up to 2 retries)
  2. Retry with simplified prompt (strip style modifiers, reduce complexity)
  3. Retry with a different model (e.g., z-image-turbo → flux2-klein)
  4. Insert placeholder (solid color rectangle with alt text)
  5. Mark slide for manual intervention

Chart Rendering Failure:
  1. Retry with same data
  2. Simplify chart type (e.g., stacked bar → simple bar)
  3. Fall back to stat-card layout (just the key number, large text)
  4. Mark slide for manual intervention

Speaker Notes Failure:
  1. Retry
  2. Generate minimal notes (just the headline and bullet points restated)
  3. Leave notes empty (the deck is still usable)

Style Guide Failure:
  1. Retry
  2. Fall back to a safe default palette (neutral grays + one accent color)
  This step MUST succeed for the pipeline to continue.

Outline Generation Failure:
  1. Retry
  2. This step MUST succeed. If it fails twice, abort the pipeline.
  There is no meaningful fallback for "no outline."
```

### 8.2 DeckContext Error Tracking

The `pipeline-state.json` records errors so the conductor can make informed retry decisions:

```json
{
  "steps": {
    "imagegen-bridge": {
      "status": "completed",
      "error": null,
      "retry_count": 0,
      "partial_failures": [
        {
          "image_id": "slide-15-hero",
          "error": "Ollama timeout after 600s",
          "retries_attempted": 2,
          "fallback_applied": "placeholder"
        }
      ]
    }
  }
}
```

### 8.3 QA-Driven Re-Invocation

When `deck-qa` finds issues, the conductor decides how to respond based on severity and category:

```
QA Finding → Conductor Decision Matrix:

Category: overlap
  error   → Re-invoke deck-assembler with adjusted layout coordinates
  warning → Log it, continue

Category: contrast
  error   → Re-invoke slide-stylist to adjust palette, then re-assemble
  warning → Log it, continue

Category: text_overflow
  error   → Re-invoke narrative-architect to shorten body_points for affected slides,
            then re-assemble
  warning → Re-invoke deck-assembler with smaller font or wider text box

Category: image_quality
  error   → Re-invoke imagegen-bridge for the affected slide(s)
  warning → Log it, continue

Category: placeholder_residue
  error   → Re-invoke deck-assembler (something was missed)
  warning → Log it, continue

Category: margin
  error   → Re-invoke deck-assembler with adjusted positions
  warning → Log it, continue
```

The conductor sets a **maximum QA iteration count** (recommended: 2). If the deck still fails QA after 2 fix-and-recheck cycles, the conductor delivers the best version with a report of outstanding issues.

### 8.4 Conductor Decision Logic: Retry vs Skip vs Abort

```
function handle_step_failure(step, error):
    state = read_pipeline_state()

    if step in CRITICAL_STEPS:  // validate-brief, narrative-architect
        if state.steps[step].retry_count < 2:
            retry(step)
        else:
            ABORT("Critical step {step} failed after retries: {error}")

    elif step in RECOVERABLE_STEPS:  // imagegen-bridge, chart-renderer, speaker-notes
        if state.steps[step].retry_count < 3:
            retry(step)
        else:
            apply_fallback(step)
            mark_step_completed_with_warnings(step)
            CONTINUE

    elif step == "deck-qa":
        // QA never causes abort — it informs retry decisions
        analyze_findings_and_decide()

    else:
        SKIP(step) and log warning
```

---

## 9. Caching Integration: DiskCache + HashFS

### Cache Architecture

The cache sits alongside the pipeline working directory but is **not** per-pipeline. It persists across pipeline runs so that regenerating a similar deck reuses previously generated assets.

```
./tmp/
├── deck/                    # Current pipeline run (ephemeral)
│   ├── pipeline-state.json
│   ├── outline.json
│   └── ...
└── cache/                   # Persistent across runs
    ├── images/              # Content-addressable image store
    │   ├── a1/b2c3d4...png  # Stored by SHA-256 hash prefix
    │   ├── f6/e5d4c3...png
    │   └── ...
    └── index.json           # Maps cache keys to content hashes
```

### Cache Key Design

The cache key is a SHA-256 hash of the inputs that determine the output:

```
cache_key = SHA-256(
    prompt           +  // The exact text prompt
    width            +  // Image dimensions
    height           +
    model_id         +  // e.g., "x/z-image-turbo:latest"
    style_tokens     +  // Sorted, joined style modifiers from StyleGuide
    steps               // Inference steps (affects quality)
)
```

**Not included in the cache key:**
- `seed` (different seeds = different images for the same prompt, which is intentional)
- `timeout` (operational, not content-affecting)
- File path (the same image can be placed anywhere)

### Cache Lookup Flow

```
function generate_image(prompt, width, height, model, style_tokens, steps):
    key = compute_cache_key(prompt, width, height, model, style_tokens, steps)

    cached = lookup_cache(key)
    if cached:
        copy_from_cache(cached.content_hash, target_path)
        return {
            "status": "cached",
            "file_path": target_path,
            "content_hash": cached.content_hash,
            "cache_key": key
        }

    // Cache miss — generate
    result = call_ollama(prompt, width, height, model, steps)
    content_hash = sha256(result.image_bytes)

    store_in_cache(key, content_hash, result.image_bytes)
    write_file(target_path, result.image_bytes)

    return {
        "status": "generated",
        "file_path": target_path,
        "content_hash": content_hash,
        "cache_key": key
    }
```

### Cache Invalidation Strategy

| Trigger | Action |
|---------|--------|
| Model version changes (user pulls a new version of `x/z-image-turbo`) | Cache keys include model ID. New version = new keys = automatic miss. However, old cache entries remain. Periodic cleanup recommended. |
| User requests fresh generation | The conductor passes a `--no-cache` flag. Skip cache lookup, always generate. |
| Cache grows too large | A cleanup script removes entries older than N days or exceeding a total size threshold. `index.json` tracks `last_accessed` timestamps. |
| Manual invalidation | Delete `./tmp/cache/index.json` and the `images/` directory. Next run rebuilds from scratch. |

### When to Check Cache

The `imagegen-bridge` skill checks the cache **before every individual image generation call**, not just at the start of the step. This means:

- If slides 1-10 are identical to a previous run but slides 11-25 are new, the first 10 serve from cache and only 11-25 are generated.
- The image-manifest records `"status": "cached"` for cache hits, so the conductor and the user can see how many assets were reused.

---

## 10. How Skills Read and Write State (Implementation Pattern)

Each skill follows the same pattern for reading dependencies and writing outputs. Since skills are invoked by Claude Code (not by a Python/Node runtime), the "read" and "write" operations are tool calls within the skill's SKILL.md instructions.

### Reading State (Skill Instructions)

Each skill's SKILL.md will include instructions like:

```markdown
## Load Dependencies

Read the following files from `./tmp/deck/`:
1. `talk-brief.json` — the user's presentation requirements
2. `style-guide.json` — the palette, fonts, and layout templates

If either file does not exist, stop and report: "Missing dependency: {filename}.
The deck-conductor must run the prerequisite skills first."

Parse the JSON and use the values throughout this skill.
```

### Writing State (Skill Instructions)

```markdown
## Save Output

Write the outline to `./tmp/deck/outline.json` using the Write tool.
Ensure the JSON is valid and matches the SlideOutline schema.

Then update `./tmp/deck/pipeline-state.json`:
- Set steps.narrative-architect.status to "completed"
- Set steps.narrative-architect.completed_at to the current ISO timestamp
- Set steps.narrative-architect.output_file to "./tmp/deck/outline.json"
- Compute the SHA-256 checksum of outline.json and set steps.narrative-architect.checksum

Use a Python one-liner or the Bash tool to compute the checksum:
```bash
python3 -c "import hashlib,sys; print('sha256:'+hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" ./tmp/deck/outline.json
```
```

### Conductor Orchestration Pattern

The deck-conductor agent's instructions will look like:

```markdown
## Pipeline Execution

For each step in the pipeline:

1. Check pipeline-state.json. If this step is already "completed" and the
   output file exists with matching checksum, skip it.

2. Invoke the skill:
   /narrative-architect

3. After the skill completes, verify:
   - The output file exists at the expected path
   - pipeline-state.json was updated

4. If the skill failed, apply the error recovery pattern for this step
   (see the fallback chains in the conductor's reference docs).

5. Proceed to the next step.
```

---

## 11. Conversation Context Strategy

While files are the source of truth, the conversation context provides useful summaries that help the conductor make decisions without reading every file.

### What Each Skill Echoes to Conversation

| Skill | Echoed Summary |
|-------|---------------|
| `validate-brief` | "Talk brief validated: {topic}, {duration}min, {audience}, {slide_count_hint} slides" |
| `slide-stylist` | "StyleGuide ready: palette={primary}/{secondary}/{accent}, fonts={heading}/{body}" |
| `narrative-architect` | "Outline ready: {N} slides, arc={arc_pattern}. Slide types: {count by type}" |
| `speaker-notes-writer` | "Speaker notes ready: {N} slides, estimated {M} minutes total" |
| `imagegen-bridge` | "Images ready: {generated}/{cached}/{placeholder}/{failed} out of {total}" |
| `chart-renderer` | "Charts ready: {N} charts rendered" |
| `deck-assembler` | "Deck assembled: {path}, {N} slides, {M} images embedded" |
| `deck-qa` | "QA verdict: {verdict}. {errors} errors, {warnings} warnings." + list of errors if any |

These summaries are concise enough to stay within conversation token limits even for large decks (30+ slides), while giving the conductor enough information to decide next steps without reading files.

---

## 12. Edge Cases and Design Decisions

### What if the user changes the talk brief mid-pipeline?

The conductor computes a SHA-256 hash of `talk-brief.json` at the start and stores it in `pipeline-state.json` as `talk_brief_hash`. If the user modifies the brief, the conductor detects the hash mismatch and either:
- Restarts the pipeline from scratch (safe default).
- Asks the user: "The talk brief has changed. Should I restart the pipeline or continue with the current state?"

### What if `./tmp/deck/` already exists from a previous run?

The conductor checks at the start. If the directory exists:
- If `pipeline-state.json` exists and `status == "completed"`: ask the user if they want to start fresh or view the previous output.
- If `pipeline-state.json` exists and `status != "completed"`: offer to resume.
- If no `pipeline-state.json`: treat as corrupt, start fresh.

### What about concurrent pipeline runs?

Not supported. Claude Code runs skills sequentially in a single conversation. If the user wants to generate two decks simultaneously, they use two Claude Code sessions with different working directories. The `./tmp/deck/` path is per-project, so there is no conflict.

### Maximum file sizes

- `talk-brief.json`: < 5 KB (always small)
- `style-guide.json`: < 10 KB
- `outline.json`: < 50 KB (even for a 60-slide deck)
- `speaker-notes.json`: < 100 KB (long notes for many slides)
- `image-manifest.json`: < 50 KB (metadata only, not image bytes)
- `pipeline-state.json`: < 10 KB
- Total JSON state: **< 225 KB** -- easily handled by file I/O

Images are the large assets (1-5 MB each). A 25-slide deck with one image per slide is 25-125 MB total. This is fine for local disk.

---

## 13. Implementation Recommendations

### Priority Order

1. **Define the directory structure and PipelineState schema first.** This is the contract that every skill depends on. Get it right before building any skills.

2. **Build a small utility script** (`src/pipeline_utils.py`) with functions for:
   - `read_state()` / `write_state()` -- read and update `pipeline-state.json`
   - `compute_checksum(file_path)` -- SHA-256 of a file
   - `compute_cache_key(prompt, width, height, model, style_tokens, steps)` -- cache key generation
   - `check_cache(key)` / `store_cache(key, content_hash, image_bytes)` -- cache operations

   Skills can call these via `python3 src/pipeline_utils.py <command> <args>` from their Bash tool invocations, keeping the logic DRY.

3. **Start with the simplest skills** (validate-brief, slide-stylist) to validate the state-passing pattern before building the complex skills (imagegen-bridge, deck-assembler).

4. **Add caching last.** Get the pipeline working end-to-end without caching first. Caching is an optimisation that adds complexity -- do not let it block the critical path.

### What Not to Build

- **No custom serialisation format.** JSON is sufficient. Do not invent a binary format or use YAML.
- **No file-watching or event system.** Skills do not need to watch for file changes. The conductor invokes them in order.
- **No schema validation library.** Claude Code skills can validate JSON structure by reading and checking fields inline. A formal JSON Schema validator (like `ajv` or `jsonschema`) is overkill for this use case -- the schemas in this document are reference definitions for humans and for Claude, not for runtime validation.
- **No database or key-value store.** Files on disk are the database.

### Naming Conventions

| Convention | Example | Rationale |
|-----------|---------|-----------|
| File names: lowercase-kebab-case | `style-guide.json` | Matches existing project conventions |
| JSON keys: snake_case | `"slide_number"` | Standard for JSON; matches README contract definitions |
| Image files: `slide-{NN}-{purpose}` | `slide-03-hero.png` | Predictable, sortable, human-readable |
| Cache files: SHA-256 prefix dirs | `a1/b2c3d4...png` | Content-addressable, avoids filename collisions |

---

## 14. Summary

| Question | Answer |
|----------|--------|
| Where is state stored? | `./tmp/deck/` directory with one JSON file per contract |
| What is the source of truth? | Files on disk, not conversation context |
| How do skills find state? | Fixed path convention: `./tmp/deck/{contract-name}.json` |
| How does resumability work? | `pipeline-state.json` tracks step completion; conductor skips completed steps |
| How are images tracked? | `image-manifest.json` with path + content hash + cache key per image |
| How does caching work? | Content-addressable store in `./tmp/cache/` keyed by SHA-256 of generation inputs |
| What happens when a skill fails? | Fallback chains per skill type; conductor retries, applies fallbacks, or aborts |
| What happens when QA fails? | Conductor re-invokes affected skills (max 2 QA cycles), then delivers best effort |
| Is this simple enough for Claude Code skills? | Yes. Every operation is a file read, file write, or shell command. No server, no daemon, no database. |
