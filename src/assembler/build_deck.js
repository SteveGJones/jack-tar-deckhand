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

        switch (slideData.slide_type) {
            case 'title':
                buildTitleSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, imageData });
                break;
            case 'section_divider':
                buildSectionDivider(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, noteData });
                break;
            case 'closing':
                buildClosingSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData });
                break;
            case 'diagram':
                buildDiagramSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, noteData, imageData });
                break;
            case 'data_chart':
                buildDataChartSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, noteData, chartData });
                break;
            case 'code':
                buildCodeSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, noteData });
                break;
            default:
                // content, two_column, icon_grid, image_feature, etc.
                buildContentSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, noteData, imageData });
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
 * Title slide: Primary bg (#006B5E), white text left, hero image right half,
 * logo bottom-left.
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

    // Logo bottom-left
    if (hasLogo) {
        const logoH = 0.55;
        const logoW = logoH * (169 / 200); // maintain aspect ratio
        slide.addImage({
            path: logoPath,
            x: MARGIN,
            y: SLIDE_H - MARGIN - logoH,
            w: logoW,
            h: logoH,
            altText: 'metamirror.io logo',
        });
    }

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

    if (noteData) {
        slide.addNotes(noteData.text);
    }
}

/**
 * Closing slide: Primary bg (#006B5E), white text, logo bottom-left.
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

    // Logo bottom-left
    if (hasLogo) {
        const logoH = 0.55;
        const logoW = logoH * (169 / 200);
        slide.addImage({
            path: logoPath,
            x: MARGIN,
            y: SLIDE_H - MARGIN - logoH,
            w: logoW,
            h: logoH,
            altText: 'metamirror.io logo',
        });
    }

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

    // Optional logo overlay (bottom-left, same position as title/closing slides)
    if (hasLogo) {
        const logoH = 0.55;
        const logoW = logoH * (169 / 200);
        slide.addImage({
            path: logoPath,
            x: MARGIN,
            y: SLIDE_H - MARGIN - logoH,
            w: logoW,
            h: logoH,
            altText: 'Logo',
        });
    }

    // Speaker notes
    if (noteData) {
        slide.addNotes(noteData.text);
    }
}

// Run
assembleDeck().catch(err => {
    console.error('Assembly failed:', err);
    process.exit(1);
});
