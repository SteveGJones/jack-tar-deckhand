#!/usr/bin/env node
/**
 * deck-assembler: Build a .pptx from DeckContext contracts.
 *
 * Reads: SlideOutline, StyleGuide, ImageManifest, ChartManifest, SpeakerNotes
 * Produces: ./tmp/deck/output/presentation.pptx
 *
 * Usage:
 *   node src/assembler/build_deck.js [--deck-dir PATH]
 *
 * Default deck-dir: ./tmp/deck
 */

const fs = require('fs');
const path = require('path');
const PptxGenJS = require('pptxgenjs');

// Parse CLI args
const args = process.argv.slice(2);
const deckDirIndex = args.indexOf('--deck-dir');
const DECK_DIR = deckDirIndex >= 0 ? path.resolve(args[deckDirIndex + 1]) : path.resolve('./tmp/deck');

/**
 * Load a DeckContext JSON contract.
 */
function loadContract(name) {
    const filePath = path.join(DECK_DIR, `${name}.json`);
    if (!fs.existsSync(filePath)) {
        console.error(`Contract not found: ${filePath}`);
        process.exit(1);
    }
    return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
}

/**
 * Resolve an image path from the manifest. Handles both absolute paths and
 * paths relative to the deck directory.
 */
function resolveImagePath(manifestPath) {
    if (path.isAbsolute(manifestPath)) {
        return manifestPath;
    }
    // Strip leading ./ or ./tmp/deck/ prefix
    const clean = manifestPath.replace(/^\.\/tmp\/deck\//, '').replace(/^\.\//, '');
    return path.resolve(DECK_DIR, clean);
}

/**
 * Find the image entry for a given slide number.
 */
function findImage(imageManifest, slideNumber) {
    return (imageManifest.images || []).find(
        img => img.slide_number === slideNumber && img.status !== 'failed'
    );
}

/**
 * Find the chart entry for a given slide number.
 */
function findChart(chartManifest, slideNumber) {
    return (chartManifest.charts || []).find(
        chart => chart.slide_number === slideNumber && chart.status !== 'failed'
    );
}

/**
 * Find speaker note for a given slide number.
 */
function findNote(speakerNotes, slideNumber) {
    return (speakerNotes.notes || []).find(n => n.slide_number === slideNumber);
}

/**
 * Format file size in human-readable format.
 */
function formatSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * Main assembly function.
 */
async function assembleDeck() {
    console.log(`Assembling deck from: ${DECK_DIR}`);

    // Load all contracts
    const outline = loadContract('outline');
    const styleGuide = loadContract('style-guide');
    const imageManifest = loadContract('image-manifest');
    const chartManifest = loadContract('chart-manifest');
    const speakerNotes = loadContract('speaker-notes');

    // Load strategy map (optional — if absent, all slides use 'composed')
    const strategyMapPath = path.join(DECK_DIR, 'strategy-map.json');
    const strategyMap = fs.existsSync(strategyMapPath)
        ? JSON.parse(fs.readFileSync(strategyMapPath, 'utf-8'))
        : null;

    // Build a lookup: slide_number -> effective strategy
    const slideStrategies = {};
    if (strategyMap) {
        for (const entry of strategyMap.slides || []) {
            slideStrategies[entry.slide_number] = entry.speaker_override || entry.strategy;
        }
    }

    // Validate image assets
    const warnings = [];
    for (const img of imageManifest.images || []) {
        const imgPath = resolveImagePath(img.file_path);
        if (!fs.existsSync(imgPath)) {
            warnings.push(`Missing image: ${img.file_path} (${img.image_id})`);
        }
    }
    if (warnings.length > 0) {
        console.warn('Image asset warnings:');
        warnings.forEach(w => console.warn(`  - ${w}`));
    }

    // Extract design tokens from StyleGuide
    const palette = styleGuide.palette;
    const typo = styleGuide.typography;
    const slidePalette = styleGuide.slide_type_palette;
    const layouts = styleGuide.layout?.templates || {};

    // Slide dimensions from StyleGuide (13.333 x 7.5 for true 16:9)
    const SLIDE_W = styleGuide.layout?.slide_width_inches || 13.333;
    const SLIDE_H = styleGuide.layout?.slide_height_inches || 7.5;
    const MARGIN = styleGuide.layout?.margin_inches || 0.6;

    // Logo path (PNG with transparency)
    const logoPath = path.resolve(DECK_DIR, 'images/logo.png');
    const hasLogo = fs.existsSync(logoPath);
    if (!hasLogo) {
        console.warn('Logo file not found at images/logo.png -- slides will omit logo');
    }

    // Create presentation
    const pptx = new PptxGenJS();

    // Set layout dimensions
    pptx.defineLayout({ name: 'DECK_16_9', width: SLIDE_W, height: SLIDE_H });
    pptx.layout = 'DECK_16_9';

    // Set theme fonts
    pptx.theme = {
        headFontFace: typo.heading_font,
        bodyFontFace: typo.body_font,
    };

    // Set presentation metadata
    pptx.author = 'Jack-Tar Deckhand Pipeline';
    pptx.title = outline.slides?.[0]?.headline || 'Presentation';
    pptx.subject = 'Draft deck assembled by deck-assembler';

    // =========================================================================
    // BUILD EACH SLIDE
    // =========================================================================

    for (const slideData of outline.slides) {
        const noteData = findNote(speakerNotes, slideData.slide_number);
        const imageData = findImage(imageManifest, slideData.slide_number);
        const chartData = findChart(chartManifest, slideData.slide_number);
        const strategy = slideStrategies[slideData.slide_number] || 'composed';

        // Strategy-first routing: keynote strategies override slide-type routing
        if (strategy === 'full_render') {
            buildFullRenderSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, imageData });
            continue;
        }
        if (strategy === 'backdrop_render' || strategy === 'background') {
            const strategyEntry = strategyMap
                ? (strategyMap.slides || []).find(e => e.slide_number === slideData.slide_number)
                : null;
            const variant = strategyEntry?.backdrop_variant || 'left_panel';
            buildBackgroundSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, imageData, variant });
            continue;
        }
        if (strategy === 'backdrop') {
            // Phase 4: will become buildBackdropSlide — stub to backdrop for now
            buildBackdropRenderSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, imageData });
            continue;
        }
        if (strategy === 'pragmatic_composition') {
            const strategyEntry = strategyMap
                ? (strategyMap.slides || []).find(e => e.slide_number === slideData.slide_number)
                : null;
            buildPragmaticSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, imageManifest, strategyEntry });
            continue;
        }

        // Composed strategy: use existing slide-type routing
        switch (slideData.slide_type) {
            case 'title':
                buildTitleSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, imageData });
                break;
            case 'section_divider':
                buildSectionDivider(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData });
                break;
            case 'closing':
                buildClosingSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData });
                break;
            case 'diagram':
                buildDiagramSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, imageData });
                break;
            case 'data_chart':
                buildDataChartSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, chartData });
                break;
            case 'code':
                buildCodeSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData });
                break;
            default:
                // content, two_column, icon_grid, image_feature, etc.
                buildContentSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, imageData });
                break;
        }
    }

    // Write output
    const outputDir = path.join(DECK_DIR, 'output');
    fs.mkdirSync(outputDir, { recursive: true });
    const outputPath = path.join(outputDir, 'presentation.pptx');
    await pptx.writeFile({ fileName: outputPath });

    // Report
    const stats = fs.statSync(outputPath);
    const sizeHuman = formatSize(stats.size);
    console.log(`\nDeck assembled successfully!`);
    console.log(`  Output: ${outputPath}`);
    console.log(`  Slides: ${outline.slides.length}`);
    console.log(`  File size: ${sizeHuman}`);
    console.log(`  Within 100MB limit: ${stats.size < 100 * 1024 * 1024}`);
    if (warnings.length > 0) {
        console.log(`  Asset warnings: ${warnings.length}`);
    }

    return { outputPath, slides: outline.slides.length, size: sizeHuman };
}

// =============================================================================
// SLIDE BUILDERS
// =============================================================================

/**
 * Add footer logo to any slide (bottom-right, consistent position on every slide).
 */
function addFooterLogo(slide, ctx) {
    const { logoPath, hasLogo, SLIDE_W, SLIDE_H, MARGIN } = ctx;
    if (!hasLogo) return;

    const logoH = 0.45;
    const logoW = logoH * (169 / 200); // maintain aspect ratio
    slide.addImage({
        path: logoPath,
        x: SLIDE_W - MARGIN - logoW,
        y: SLIDE_H - MARGIN - logoH,
        w: logoW,
        h: logoH,
        altText: 'Logo',
    });
}

/**
 * Title slide: Primary bg (#006B5E), white text left, hero image right half,
 * logo bottom-right.
 */
function buildTitleSlide(pptx, slideData, ctx) {
    const { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, imageData } = ctx;
    const bgColor = slidePalette?.title_slide?.background || palette.primary;
    const textColor = slidePalette?.title_slide?.text || 'FFFFFF';

    const slide = pptx.addSlide();
    slide.background = { color: bgColor };

    // Text zone (left side) -- from StyleGuide layout template, adjusted for safe margins
    const titleSafeX = Math.max(MARGIN, SLIDE_W * 0.05);
    const textZone = layouts.title_slide?.text_zone || { x: titleSafeX, y: 1.0, w: 6.0, h: 4.5 };

    // Title text
    slide.addText(slideData.headline, {
        x: titleSafeX,
        y: textZone.y,
        w: textZone.w,
        h: 2.0,
        fontSize: typo.heading_sizes?.title_slide || 44,
        fontFace: typo.heading_font,
        color: textColor,
        bold: true,
        valign: 'bottom',
        wrap: true,
    });

    // Subtitle / body points -- use white text for projection contrast
    if (slideData.body_points && slideData.body_points.length > 0) {
        const subtitleText = slideData.body_points.join('\n');
        slide.addText(subtitleText, {
            x: titleSafeX,
            y: textZone.y + 2.5,
            w: textZone.w,
            h: 1.5,
            fontSize: typo.heading_sizes?.subheading || 24,
            fontFace: typo.body_font,
            color: textColor,
            valign: 'top',
        });
    }

    // Hero image (right half) -- use cover to fill the zone, crop excess
    if (imageData) {
        const imgPath = resolveImagePath(imageData.file_path);
        if (fs.existsSync(imgPath)) {
            const imgZone = layouts.title_slide?.image_zone || { x: 6.8, y: 0, w: 6.533, h: 7.5 };
            // For the title hero, we want the image to fill the zone (cover/crop),
            // but we need to set w/h to the zone dimensions with cover sizing
            slide.addImage({
                path: imgPath,
                x: imgZone.x,
                y: imgZone.y,
                w: imgZone.w,
                h: imgZone.h,
                sizing: { type: 'cover', w: imgZone.w, h: imgZone.h },
                altText: imageData.alt_text || '',
            });
        }
    }

    // Footer logo (bottom-right, every slide)
    addFooterLogo(slide, ctx);

    // Speaker notes
    if (noteData) {
        slide.addNotes(noteData.text);
    }
}

/**
 * Content slide: White bg (#F5FBF7), text left, image right, teal accent bar
 * left edge (#006B5E).
 */
function buildContentSlide(pptx, slideData, ctx) {
    const { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, noteData, imageData } = ctx;
    const bgColor = slidePalette?.content_slides?.background || palette.background;
    const textColor = slidePalette?.content_slides?.text || palette.text_primary;
    const accentColor = slidePalette?.content_slides?.accent_bar || palette.primary;

    const slide = pptx.addSlide();
    slide.background = { color: bgColor };

    // Teal accent bar on left edge
    slide.addShape(pptx.ShapeType.rect, {
        x: 0,
        y: 0,
        w: 0.08,
        h: SLIDE_H,
        fill: { color: accentColor },
    });

    // Determine layout based on whether there's an image
    const hasImage = imageData && fs.existsSync(resolveImagePath(imageData.file_path));
    const layoutKey = hasImage ? 'content_with_image' : 'content_only';
    const layout = layouts[layoutKey] || {};
    const textZone = layout.text_zone || { x: 0.6, y: 1.2, w: hasImage ? 6.0 : 12.133, h: 5.5 };

    // Safe margins: 5% of slide dimensions ensures no element bleeds to edge
    const safeX = Math.max(textZone.x, SLIDE_W * 0.05);
    const safeY = Math.max(MARGIN, SLIDE_H * 0.05);
    const safeMaxW = SLIDE_W - 2 * safeX;

    // Heading -- respect layout template's text zone y, but no higher than safe margin
    const headingY = Math.max(textZone.y, safeY);
    const headingH = 0.8;
    const headingW = hasImage ? Math.min(textZone.w, safeMaxW) : safeMaxW;
    slide.addText(slideData.headline, {
        x: safeX,
        y: headingY,
        w: headingW,
        h: headingH,
        fontSize: typo.heading_sizes?.slide_heading || 32,
        fontFace: typo.heading_font,
        color: textColor,
        bold: true,
        valign: 'bottom',
    });

    // Body points -- start below heading with gap to prevent overlap
    const bodyY = headingY + headingH + 0.15;
    const bodyH = SLIDE_H - bodyY - safeY;
    if (slideData.body_points && slideData.body_points.length > 0) {
        const bodyText = slideData.body_points.map(bp => ({
            text: bp,
            options: {
                fontSize: typo.body_size || 18,
                fontFace: typo.body_font,
                color: textColor,
                bullet: { type: 'bullet' },
                lineSpacingMultiple: typo.line_spacing || 1.4,
                breakLine: true,
                paraSpaceAfter: 8,
            },
        }));
        slide.addText(bodyText, {
            x: safeX,
            y: bodyY,
            w: headingW,
            h: bodyH,
            valign: 'top',
        });
    }

    // Image (right side) -- use aspect-preserving dimensions
    if (hasImage) {
        const imgPath = resolveImagePath(imageData.file_path);
        const imgZone = layout.image_zone || { x: 7.0, y: 0.8, w: 5.7, h: 5.9 };
        // Calculate image dimensions to preserve 16:9 aspect ratio within zone
        const imgNativeRatio = (imageData.dimensions?.width || 1024) / (imageData.dimensions?.height || 576);
        const zoneRatio = imgZone.w / imgZone.h;
        let imgW, imgH, imgX, imgY;
        if (imgNativeRatio > zoneRatio) {
            // Image wider than zone -- fit to width
            imgW = imgZone.w;
            imgH = imgZone.w / imgNativeRatio;
            imgX = imgZone.x;
            imgY = imgZone.y + (imgZone.h - imgH) / 2;
        } else {
            // Image taller than zone -- fit to height
            imgH = imgZone.h;
            imgW = imgZone.h * imgNativeRatio;
            imgX = imgZone.x + (imgZone.w - imgW) / 2;
            imgY = imgZone.y;
        }
        slide.addImage({
            path: imgPath,
            x: imgX,
            y: imgY,
            w: imgW,
            h: imgH,
            altText: imageData.alt_text || '',
        });
    }

    // Footer logo (bottom-right, every slide)
    addFooterLogo(slide, ctx);

    // Speaker notes
    if (noteData) {
        slide.addNotes(noteData.text);
    }
}

/**
 * Section divider: Primary Container bg (#7AF8DB), bold centred dark text.
 */
function buildSectionDivider(pptx, slideData, ctx) {
    const { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, noteData } = ctx;
    const bgColor = slidePalette?.section_dividers?.background || palette.background_alt;
    const textColor = slidePalette?.section_dividers?.text || palette.text_primary;

    const slide = pptx.addSlide();
    slide.background = { color: bgColor };

    const textZone = layouts.section_divider?.text_zone || { x: 1.5, y: 2.0, w: 10.333, h: 3.5 };

    slide.addText(slideData.headline, {
        x: textZone.x,
        y: textZone.y,
        w: textZone.w,
        h: textZone.h,
        fontSize: typo.heading_sizes?.section_divider || 36,
        fontFace: typo.heading_font,
        color: textColor,
        align: 'center',
        valign: 'middle',
        bold: true,
        wrap: true,
    });

    // Footer logo (bottom-right, every slide)
    addFooterLogo(slide, ctx);

    // Speaker notes
    if (noteData) {
        slide.addNotes(noteData.text);
    }
}

/**
 * Architecture/Diagram slide: White bg, small heading top, large image zone.
 */
function buildDiagramSlide(pptx, slideData, ctx) {
    const { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, noteData, imageData } = ctx;
    const bgColor = slidePalette?.content_slides?.background || palette.background;
    const textColor = slidePalette?.content_slides?.text || palette.text_primary;
    const accentColor = slidePalette?.content_slides?.accent_bar || palette.primary;

    const slide = pptx.addSlide();
    slide.background = { color: bgColor };

    // Teal accent bar on left edge
    slide.addShape(pptx.ShapeType.rect, {
        x: 0,
        y: 0,
        w: 0.08,
        h: SLIDE_H,
        fill: { color: accentColor },
    });

    const layout = layouts.architecture_diagram || {};
    const textZone = layout.text_zone || { x: 0.6, y: 0.4, w: 12.133, h: 1.2 };
    const imgZone = layout.image_zone || { x: 0.6, y: 1.8, w: 12.133, h: 5.2 };
    const diagSafeX = Math.max(textZone.x, SLIDE_W * 0.05);
    const diagSafeY = Math.max(textZone.y, SLIDE_H * 0.05);
    const diagSafeMaxW = Math.min(textZone.w, SLIDE_W - 2 * diagSafeX);

    // Small heading at top -- respect layout template position
    slide.addText(slideData.headline, {
        x: diagSafeX,
        y: diagSafeY,
        w: diagSafeMaxW,
        h: textZone.h,
        fontSize: typo.heading_sizes?.slide_heading || 32,
        fontFace: typo.heading_font,
        color: textColor,
        bold: true,
        valign: 'bottom',
    });

    // Body points (compact, below heading)
    if (slideData.body_points && slideData.body_points.length > 0) {
        // For diagram slides, put body text as compact list on left, diagram on right
        const bodyText = slideData.body_points.map(bp => ({
            text: bp,
            options: {
                fontSize: 18,
                fontFace: typo.body_font,
                color: textColor,
                bullet: { type: 'bullet' },
                lineSpacingMultiple: 1.3,
                breakLine: true,
                paraSpaceAfter: 4,
            },
        }));
        // Split layout: body text left ~45%, diagram image right ~55%
        const bodyW = imgZone.w * 0.45;
        const diagramX = diagSafeX + bodyW + 0.2;
        const diagramW = imgZone.x + imgZone.w - diagramX;

        slide.addText(bodyText, {
            x: diagSafeX,
            y: imgZone.y,
            w: bodyW,
            h: imgZone.h,
            valign: 'top',
        });

        // Diagram image (right portion) -- preserve aspect ratio
        if (imageData) {
            const imgPath = resolveImagePath(imageData.file_path);
            if (fs.existsSync(imgPath)) {
                const diagramZoneH = imgZone.h;
                const imgRatio = (imageData.dimensions?.width || 1024) / (imageData.dimensions?.height || 768);
                const zoneRatio = diagramW / diagramZoneH;
                let dW, dH, dX, dY;
                if (imgRatio > zoneRatio) {
                    dW = diagramW;
                    dH = diagramW / imgRatio;
                    dX = diagramX;
                    dY = imgZone.y + (diagramZoneH - dH) / 2;
                } else {
                    dH = diagramZoneH;
                    dW = diagramZoneH * imgRatio;
                    dX = diagramX + (diagramW - dW) / 2;
                    dY = imgZone.y;
                }
                slide.addImage({
                    path: imgPath,
                    x: dX,
                    y: dY,
                    w: dW,
                    h: dH,
                    altText: imageData.alt_text || '',
                });
            }
        }
    } else {
        // No body points -- full-width diagram
        if (imageData) {
            const imgPath = resolveImagePath(imageData.file_path);
            if (fs.existsSync(imgPath)) {
                slide.addImage({
                    path: imgPath,
                    x: imgZone.x,
                    y: imgZone.y,
                    w: imgZone.w,
                    h: imgZone.h,
                    sizing: { type: 'contain', w: imgZone.w, h: imgZone.h },
                    altText: imageData.alt_text || '',
                });
            }
        }
    }

    // Footer logo (bottom-right, every slide)
    addFooterLogo(slide, ctx);

    // Speaker notes
    if (noteData) {
        slide.addNotes(noteData.text);
    }
}

/**
 * Data chart slide: White bg, heading, chart image below.
 */
function buildDataChartSlide(pptx, slideData, ctx) {
    const { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, noteData, chartData } = ctx;
    const bgColor = slidePalette?.content_slides?.background || palette.background;
    const textColor = slidePalette?.content_slides?.text || palette.text_primary;
    const accentColor = slidePalette?.content_slides?.accent_bar || palette.primary;

    const slide = pptx.addSlide();
    slide.background = { color: bgColor };

    // Teal accent bar
    slide.addShape(pptx.ShapeType.rect, {
        x: 0, y: 0, w: 0.08, h: SLIDE_H,
        fill: { color: accentColor },
    });

    // Reuse architecture_diagram layout (same heading + large image pattern)
    const layout = layouts.architecture_diagram || {};
    const textZone = layout.text_zone || { x: 0.6, y: 0.4, w: 12.133, h: 1.2 };
    const imgZone = layout.image_zone || { x: 0.6, y: 1.8, w: 12.133, h: 5.2 };
    const safeX = Math.max(textZone.x, SLIDE_W * 0.05);
    const safeY = Math.max(MARGIN, SLIDE_H * 0.05);

    // Heading -- respect layout template position
    const headingY = Math.max(textZone.y, safeY);
    const headingH = textZone.h;
    const headingW = Math.min(textZone.w, SLIDE_W - 2 * safeX);
    slide.addText(slideData.headline, {
        x: safeX,
        y: headingY,
        w: headingW,
        h: headingH,
        fontSize: typo.heading_sizes?.slide_heading || 32,
        fontFace: typo.heading_font,
        color: textColor,
        bold: true,
    });

    // Chart image -- use layout image zone
    if (chartData) {
        const chartPath = resolveImagePath(chartData.file_path);
        if (fs.existsSync(chartPath)) {
            slide.addImage({
                path: chartPath,
                x: imgZone.x,
                y: imgZone.y,
                w: imgZone.w,
                h: imgZone.h,
                sizing: { type: 'contain', w: imgZone.w, h: imgZone.h },
                altText: chartData.alt_text || 'Data chart',
            });
        }
    }

    // Footer logo (bottom-right, every slide)
    addFooterLogo(slide, ctx);

    if (noteData) {
        slide.addNotes(noteData.text);
    }
}

/**
 * Code slide: Dark Surface bg (#0E1513), mono font, light text.
 */
function buildCodeSlide(pptx, slideData, ctx) {
    const { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, noteData } = ctx;
    const bgColor = slidePalette?.code_slides?.background || '0E1513';
    const textColor = slidePalette?.code_slides?.text || palette.text_on_dark;

    const slide = pptx.addSlide();
    slide.background = { color: bgColor };

    const layout = layouts.code_slide || {};
    const textZone = layout.text_zone || { x: 0.6, y: 1.2, w: 12.133, h: 5.5 };
    const safeX = Math.max(textZone.x, SLIDE_W * 0.05);
    const safeY = Math.max(MARGIN, SLIDE_H * 0.05);

    // Heading -- respect layout template's text zone y
    const headingY = Math.max(textZone.y, safeY);
    const headingH = 0.9;
    const headingW = Math.min(textZone.w, SLIDE_W - 2 * safeX);
    slide.addText(slideData.headline, {
        x: safeX,
        y: headingY,
        w: headingW,
        h: headingH,
        fontSize: typo.heading_sizes?.slide_heading || 32,
        fontFace: typo.heading_font,
        color: textColor,
        bold: true,
    });

    // Code body in mono font -- positioned relative to heading bottom
    if (slideData.body_points && slideData.body_points.length > 0) {
        const codeText = slideData.body_points.join('\n');
        const bodyY = headingY + headingH + 0.15;
        const bodyH = SLIDE_H - bodyY - safeY;
        slide.addText(codeText, {
            x: safeX,
            y: bodyY,
            w: headingW,
            h: bodyH,
            fontSize: 16,
            fontFace: typo.mono_font || 'JetBrains Mono',
            color: textColor,
            valign: 'top',
        });
    }

    // Footer logo (bottom-right, every slide)
    addFooterLogo(slide, ctx);

    if (noteData) {
        slide.addNotes(noteData.text);
    }
}

/**
 * Closing slide: Primary bg (#006B5E), white text, logo bottom-right.
 */
function buildClosingSlide(pptx, slideData, ctx) {
    const { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData } = ctx;
    const bgColor = slidePalette?.closing_slide?.background || palette.primary;
    const textColor = slidePalette?.closing_slide?.text || 'FFFFFF';

    const slide = pptx.addSlide();
    slide.background = { color: bgColor };

    const textZone = layouts.closing_slide?.text_zone || { x: 1.5, y: 1.5, w: 10.333, h: 4.5 };

    // Headline
    slide.addText(slideData.headline, {
        x: textZone.x,
        y: textZone.y,
        w: textZone.w,
        h: 1.8,
        fontSize: typo.heading_sizes?.title_slide || 44,
        fontFace: typo.heading_font,
        color: textColor,
        align: 'center',
        valign: 'middle',
        bold: true,
    });

    // Body points (links, contact info) -- white text for projection contrast
    if (slideData.body_points && slideData.body_points.length > 0) {
        const closingText = slideData.body_points.map(bp => ({
            text: bp,
            options: {
                fontSize: typo.body_size || 18,
                fontFace: typo.body_font,
                color: textColor,
                breakLine: true,
                paraSpaceAfter: 12,
            },
        }));
        slide.addText(closingText, {
            x: textZone.x,
            y: textZone.y + 2.2,
            w: textZone.w,
            h: 2.3,
            align: 'center',
            valign: 'top',
        });
    }

    // Footer logo (bottom-right, every slide)
    addFooterLogo(slide, ctx);

    if (noteData) {
        slide.addNotes(noteData.text);
    }
}

/**
 * Full-render keynote slide: entire slide is a single AI-generated image.
 * No text boxes, no shapes — just a full-bleed image + speaker notes.
 * Logo overlay is optional (controlled by style guide).
 */
function buildFullRenderSlide(pptx, slideData, ctx) {
    const { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, imageData } = ctx;

    const slide = pptx.addSlide();

    // Full-bleed image covering the entire slide
    if (imageData) {
        const imgPath = resolveImagePath(imageData.file_path);
        if (fs.existsSync(imgPath)) {
            slide.addImage({
                path: imgPath,
                x: 0,
                y: 0,
                w: SLIDE_W,
                h: SLIDE_H,
                sizing: { type: 'cover', w: SLIDE_W, h: SLIDE_H },
                altText: imageData.alt_text || '',
            });
        }
    }

    // Footer logo (bottom-right, every slide)
    addFooterLogo(slide, ctx);

    // Speaker notes
    if (noteData) {
        slide.addNotes(noteData.text);
    }
}

/**
 * Backdrop-render keynote slide: AI-generated background image with
 * programmatic text overlay. Text remains editable in PowerPoint.
 * A semi-transparent backing rectangle ensures text readability.
 */
function buildBackdropRenderSlide(pptx, slideData, ctx) {
    const { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, noteData, imageData } = ctx;
    const textColor = slidePalette?.content_slides?.text || palette.text_primary;

    const slide = pptx.addSlide();

    // Full-bleed backdrop image
    if (imageData) {
        const imgPath = resolveImagePath(imageData.file_path);
        if (fs.existsSync(imgPath)) {
            slide.addImage({
                path: imgPath,
                x: 0,
                y: 0,
                w: SLIDE_W,
                h: SLIDE_H,
                sizing: { type: 'cover', w: SLIDE_W, h: SLIDE_H },
                altText: imageData.alt_text || '',
            });
        }
    }

    // Semi-transparent text backing — left third of the slide
    const textZoneW = SLIDE_W * 0.45;
    slide.addShape(pptx.ShapeType.rect, {
        x: 0,
        y: 0,
        w: textZoneW,
        h: SLIDE_H,
        fill: { color: '000000', transparency: 60 },
    });

    // Heading — white text for contrast against the dark backing
    const safeX = MARGIN;
    const headingY = Math.max(SLIDE_H * 0.15, MARGIN);
    const headingW = textZoneW - 2 * MARGIN;
    slide.addText(slideData.headline, {
        x: safeX,
        y: headingY,
        w: headingW,
        h: 1.0,
        fontSize: typo.heading_sizes?.slide_heading || 32,
        fontFace: typo.heading_font,
        color: 'FFFFFF',
        bold: true,
        valign: 'bottom',
        wrap: true,
    });

    // Body points — white text
    if (slideData.body_points && slideData.body_points.length > 0) {
        const bodyY = headingY + 1.2;
        const bodyH = SLIDE_H - bodyY - MARGIN;
        const bodyText = slideData.body_points.map(bp => ({
            text: bp,
            options: {
                fontSize: typo.body_size || 18,
                fontFace: typo.body_font,
                color: 'FFFFFF',
                bullet: { type: 'bullet' },
                lineSpacingMultiple: typo.line_spacing || 1.4,
                breakLine: true,
                paraSpaceAfter: 8,
            },
        }));
        slide.addText(bodyText, {
            x: safeX,
            y: bodyY,
            w: headingW,
            h: bodyH,
            valign: 'top',
        });
    }

    // Footer logo (bottom-right, every slide)
    addFooterLogo(slide, ctx);

    // Speaker notes
    if (noteData) {
        slide.addNotes(noteData.text);
    }
}

/**
 * Background slide: AI background image + text in a template zone overlay.
 * Supports 5 variants: left_panel, right_panel, bottom_bar, top_band, center_float.
 */
function buildBackgroundSlide(pptx, slideData, ctx) {
    const { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, imageData, variant } = ctx;

    const slide = pptx.addSlide();

    // Full-bleed backdrop image
    if (imageData) {
        const imgPath = resolveImagePath(imageData.file_path);
        if (fs.existsSync(imgPath)) {
            slide.addImage({
                path: imgPath, x: 0, y: 0, w: SLIDE_W, h: SLIDE_H,
                sizing: { type: 'cover', w: SLIDE_W, h: SLIDE_H },
                altText: imageData.alt_text || '',
            });
        }
    }

    // Template zone definitions (in inches)
    const zones = {
        left_panel:   { ox: 0,              oy: 0,              ow: SLIDE_W * 0.40, oh: SLIDE_H,          tx: MARGIN,                        ty: SLIDE_H * 0.15, tw: SLIDE_W * 0.40 - 2 * MARGIN, transparency: 60 },
        right_panel:  { ox: SLIDE_W * 0.60, oy: 0,              ow: SLIDE_W * 0.40, oh: SLIDE_H,          tx: SLIDE_W * 0.60 + MARGIN,       ty: SLIDE_H * 0.15, tw: SLIDE_W * 0.40 - 2 * MARGIN, transparency: 60 },
        bottom_bar:   { ox: 0,              oy: SLIDE_H * 0.70, ow: SLIDE_W,         oh: SLIDE_H * 0.30,  tx: MARGIN,                        ty: SLIDE_H * 0.72, tw: SLIDE_W - 2 * MARGIN,        transparency: 60 },
        top_band:     { ox: 0,              oy: 0,              ow: SLIDE_W,         oh: SLIDE_H * 0.25,  tx: MARGIN,                        ty: MARGIN,          tw: SLIDE_W - 2 * MARGIN,        transparency: 60 },
        center_float: { ox: SLIDE_W * 0.20, oy: SLIDE_H * 0.25, ow: SLIDE_W * 0.60, oh: SLIDE_H * 0.50, tx: SLIDE_W * 0.20 + MARGIN,       ty: SLIDE_H * 0.27, tw: SLIDE_W * 0.60 - 2 * MARGIN, transparency: 65 },
    };

    const zone = zones[variant] || zones.left_panel;

    // Semi-transparent overlay
    slide.addShape(pptx.ShapeType.rect, {
        x: zone.ox, y: zone.oy, w: zone.ow, h: zone.oh,
        fill: { color: '000000', transparency: zone.transparency },
    });

    // Heading
    const headingH = 1.0;
    slide.addText(slideData.headline, {
        x: zone.tx, y: zone.ty, w: zone.tw, h: headingH,
        fontSize: typo.heading_sizes?.slide_heading || 32,
        fontFace: typo.heading_font,
        color: 'FFFFFF',
        bold: true,
        valign: 'bottom',
        wrap: true,
    });

    // Body points
    if (slideData.body_points && slideData.body_points.length > 0) {
        const bodyY = zone.ty + headingH + 0.15;
        const bodyH = (zone.oy + zone.oh) - bodyY - MARGIN;
        const bodyText = slideData.body_points.map(bp => ({
            text: bp,
            options: {
                fontSize: typo.body_size || 18,
                fontFace: typo.body_font,
                color: 'FFFFFF',
                bullet: { type: 'bullet' },
                lineSpacingMultiple: typo.line_spacing || 1.4,
                breakLine: true,
                paraSpaceAfter: 8,
            },
        }));
        slide.addText(bodyText, {
            x: zone.tx, y: bodyY, w: zone.tw, h: Math.max(bodyH, 1.0),
            valign: 'top',
        });
    }

    // Footer logo
    addFooterLogo(slide, ctx);

    // Speaker notes
    if (noteData) {
        slide.addNotes(noteData.text);
    }
}

/**
 * Find all images for a given slide number from the manifest.
 */
function findSlideImages(imageManifest, slideNumber) {
    return (imageManifest.images || []).filter(
        img => img.slide_number === slideNumber && img.status !== 'failed'
    );
}

/**
 * Pragmatic composition slide: atmospheric background + individually-placed element images
 * with text labels adjacent to each element.
 */
function buildPragmaticSlide(pptx, slideData, ctx) {
    const { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, imageManifest, strategyEntry } = ctx;

    const slide = pptx.addSlide();
    const elementLayout = strategyEntry?.element_layout || {};
    const elements = elementLayout.elements || [];
    const titleRegion = elementLayout.title_region || { x: 0.05, y: 0.03, w: 0.90, h: 0.12 };
    const images = findSlideImages(imageManifest, slideData.slide_number);

    // 1. Background image (full-bleed)
    const bgImage = images.find(img => img.placement_zone === 'background');
    if (bgImage) {
        const imgPath = resolveImagePath(bgImage.file_path);
        if (fs.existsSync(imgPath)) {
            slide.addImage({
                path: imgPath, x: 0, y: 0, w: SLIDE_W, h: SLIDE_H,
                sizing: { type: 'cover', w: SLIDE_W, h: SLIDE_H },
                altText: 'Background',
            });
        }
    }

    // 2. Place each element image at its prescribed position
    for (const elem of elements) {
        const elemImage = images.find(img => img.element_id === elem.id);
        const ex = elem.x * SLIDE_W;
        const ey = elem.y * SLIDE_H;
        const ew = elem.w * SLIDE_W;
        const eh = elem.h * SLIDE_H;

        if (elemImage) {
            const imgPath = resolveImagePath(elemImage.file_path);
            if (fs.existsSync(imgPath)) {
                slide.addImage({
                    path: imgPath, x: ex, y: ey, w: ew, h: eh,
                    sizing: { type: 'contain', w: ew, h: eh },
                    altText: elem.id,
                });
            }
        }

        // 3. Text label — below element (or above if in bottom third)
        const labelSource = elem.label_source || '';
        const match = labelSource.match(/body_points\[(\d+)\]/);
        const label = match && slideData.body_points
            ? (slideData.body_points[parseInt(match[1])] || elem.id)
            : elem.id;

        const labelH = 0.5;
        const labelW = ew;
        const inBottomThird = (ey + eh) > (SLIDE_H * 0.67);
        const labelY = inBottomThird ? (ey - labelH - 0.05) : (ey + eh + 0.05);
        const labelX = ex;

        // Small backing pill
        slide.addShape(pptx.ShapeType.rect, {
            x: labelX, y: labelY, w: labelW, h: labelH,
            fill: { color: '000000', transparency: 55 },
            rectRadius: 0.1,
        });

        slide.addText(label, {
            x: labelX, y: labelY, w: labelW, h: labelH,
            fontSize: typo.body_size || 18,
            fontFace: typo.body_font,
            color: 'FFFFFF',
            align: 'center',
            valign: 'middle',
            bold: true,
            wrap: true,
        });
    }

    // 4. Headline in title region
    slide.addText(slideData.headline, {
        x: titleRegion.x * SLIDE_W,
        y: titleRegion.y * SLIDE_H,
        w: titleRegion.w * SLIDE_W,
        h: titleRegion.h * SLIDE_H,
        fontSize: typo.heading_sizes?.slide_heading || 32,
        fontFace: typo.heading_font,
        color: 'FFFFFF',
        bold: true,
        valign: 'middle',
    });

    // Footer logo + notes
    addFooterLogo(slide, ctx);
    if (noteData) {
        slide.addNotes(noteData.text);
    }
}

// Run
assembleDeck().catch(err => {
    console.error('Assembly failed:', err);
    process.exit(1);
});
