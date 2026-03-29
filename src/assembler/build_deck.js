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
const { registerSlideMasters, SLIDE_TYPE_TO_MASTER, SLIDE_WIDTH, SLIDE_HEIGHT, MARGIN } = require('./slide_masters');
const { shouldProgressiveBuild, generateBulletBuild } = require('./progressive_builds');
const { reportFileSize, validateImageAssets } = require('./optimise');

// Parse CLI args
const args = process.argv.slice(2);
const deckDirIndex = args.indexOf('--deck-dir');
const DECK_DIR = deckDirIndex >= 0 ? args[deckDirIndex + 1] : './tmp/deck';

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
 * Resolve an image path from the manifest relative to deck dir.
 */
function resolveImagePath(manifestPath) {
    const relativePath = manifestPath.replace(/^\.\/tmp\/deck\//, '');
    return path.resolve(DECK_DIR, relativePath);
}

/**
 * Find the image entry for a given slide number and placement zone.
 */
function findImage(imageManifest, slideNumber, zone) {
    return (imageManifest.images || []).find(
        img => img.slide_number === slideNumber &&
               img.status !== 'failed' &&
               (!zone || img.placement_zone === zone)
    );
}

/**
 * Find the chart entry for a given slide number.
 */
function findChart(chartManifest, slideNumber) {
    return (chartManifest.charts || []).find(
        chart => chart.slide_number === slideNumber &&
                 chart.status !== 'failed'
    );
}

/**
 * Find speaker note for a given slide number.
 */
function findNote(speakerNotes, slideNumber) {
    return (speakerNotes.notes || []).find(n => n.slide_number === slideNumber);
}

/**
 * Build a single slide based on its type and data.
 */
function buildSlide(pptx, slideData, styleGuide, imageManifest, chartManifest, speakerNotes) {
    const masterName = SLIDE_TYPE_TO_MASTER[slideData.slide_type] || 'MASTER_CONTENT';
    const palette = styleGuide.palette;
    const typo = styleGuide.typography;
    const noteData = findNote(speakerNotes, slideData.slide_number);
    const imageData = findImage(imageManifest, slideData.slide_number);
    const chartData = findChart(chartManifest, slideData.slide_number);

    // Check for progressive build
    if (shouldProgressiveBuild(slideData, noteData)) {
        return generateBulletBuild(pptx, slideData, styleGuide, masterName, noteData);
    }

    const slide = pptx.addSlide({ masterName });

    // --- Slide type-specific content ---

    switch (slideData.slide_type) {
        case 'title':
            slide.addText(slideData.headline, {
                x: 1.0, y: 1.5, w: 8.0, h: 1.5,
                fontSize: typo.heading_sizes?.title_slide || 44,
                fontFace: typo.heading_font,
                color: palette.text_on_dark || 'FFFFFF',
                align: 'center', valign: 'bottom', bold: true,
            });
            if (slideData.body_points && slideData.body_points.length > 0) {
                slide.addText(slideData.body_points[0], {
                    x: 1.5, y: 3.2, w: 7.0, h: 1.0,
                    fontSize: typo.heading_sizes?.subheading || 20,
                    fontFace: typo.body_font,
                    color: palette.text_muted || '718096',
                    align: 'center',
                });
            }
            break;

        case 'section_divider':
            slide.addText(slideData.headline, {
                x: 1.0, y: 1.8, w: 8.0, h: 1.5,
                fontSize: typo.heading_sizes?.section_divider || 36,
                fontFace: typo.heading_font,
                color: palette.text_on_dark || 'FFFFFF',
                align: 'center', valign: 'middle', bold: true,
            });
            break;

        case 'content':
        case 'two_column':
        case 'icon_grid':
        case 'diagram':
            // Heading
            slide.addText(slideData.headline, {
                x: MARGIN, y: MARGIN, w: 9.0, h: 0.8,
                fontSize: typo.heading_sizes?.slide_heading || 28,
                fontFace: typo.heading_font,
                color: palette.text_primary,
                bold: true,
            });
            // Body points
            if (slideData.body_points && slideData.body_points.length > 0) {
                const textZoneW = imageData ? 5.0 : 8.5;
                const bodyText = slideData.body_points.map(bp => ({
                    text: bp,
                    options: {
                        fontSize: typo.body_size || 16,
                        fontFace: typo.body_font,
                        color: palette.text_primary,
                        bullet: true,
                        lineSpacingMultiple: typo.line_spacing || 1.4,
                        breakLine: true,
                    },
                }));
                slide.addText(bodyText, {
                    x: MARGIN, y: 1.5, w: textZoneW, h: 3.625,
                    valign: 'top',
                });
            }
            break;

        case 'stat_callout':
            slide.addText(slideData.headline, {
                x: 1.0, y: 1.0, w: 8.0, h: 2.5,
                fontSize: 72,
                fontFace: typo.heading_font,
                color: palette.accent || palette.primary,
                align: 'center', valign: 'middle', bold: true,
            });
            if (slideData.body_points && slideData.body_points[0]) {
                slide.addText(slideData.body_points[0], {
                    x: 1.5, y: 3.5, w: 7.0, h: 1.0,
                    fontSize: typo.body_size || 16,
                    fontFace: typo.body_font,
                    color: palette.text_on_dark || 'FFFFFF',
                    align: 'center',
                });
            }
            break;

        case 'quote':
            slide.addText(`\u201C${slideData.headline}\u201D`, {
                x: 1.0, y: 1.2, w: 8.0, h: 2.5,
                fontSize: 24,
                fontFace: typo.heading_font,
                color: palette.text_on_dark || 'FFFFFF',
                align: 'center', valign: 'middle', italic: true,
            });
            if (slideData.body_points && slideData.body_points[0]) {
                slide.addText(`\u2014 ${slideData.body_points[0]}`, {
                    x: 2.0, y: 3.8, w: 6.0, h: 0.6,
                    fontSize: 14,
                    fontFace: typo.body_font,
                    color: palette.text_muted || '718096',
                    align: 'right',
                });
            }
            break;

        case 'data_chart':
            slide.addText(slideData.headline, {
                x: MARGIN, y: MARGIN, w: 9.0, h: 0.8,
                fontSize: typo.heading_sizes?.slide_heading || 28,
                fontFace: typo.heading_font,
                color: palette.text_primary,
                bold: true,
            });
            if (chartData) {
                const chartPath = resolveImagePath(chartData.file_path);
                if (fs.existsSync(chartPath)) {
                    slide.addImage({
                        path: chartPath,
                        x: 0.75, y: 1.5, w: 8.5, h: 3.75,
                        sizing: { type: 'contain', w: 8.5, h: 3.75 },
                        altText: chartData.alt_text || 'Data chart',
                    });
                }
            }
            break;

        case 'closing':
            slide.addText(slideData.headline, {
                x: 1.0, y: 1.5, w: 8.0, h: 1.5,
                fontSize: typo.heading_sizes?.title_slide || 44,
                fontFace: typo.heading_font,
                color: palette.text_on_dark || 'FFFFFF',
                align: 'center', valign: 'middle', bold: true,
            });
            if (slideData.body_points && slideData.body_points.length > 0) {
                const closingText = slideData.body_points.map(bp => ({
                    text: bp,
                    options: {
                        fontSize: typo.body_size || 16,
                        fontFace: typo.body_font,
                        color: palette.text_on_dark || 'FFFFFF',
                        bullet: true,
                        breakLine: true,
                    },
                }));
                slide.addText(closingText, {
                    x: 1.5, y: 3.2, w: 7.0, h: 2.0,
                    valign: 'top',
                });
            }
            break;

        case 'image_feature':
        case 'blank_visual':
        default:
            if (slideData.headline) {
                slide.addText(slideData.headline, {
                    x: MARGIN, y: MARGIN, w: 9.0, h: 0.8,
                    fontSize: typo.heading_sizes?.slide_heading || 28,
                    fontFace: typo.heading_font,
                    color: palette.text_primary,
                    bold: true,
                });
            }
            break;
    }

    // --- Image placement (for any slide type) ---
    if (imageData && imageData.status !== 'failed') {
        const imgPath = resolveImagePath(imageData.file_path);
        if (fs.existsSync(imgPath)) {
            const zone = imageData.placement_zone || 'image_zone';
            if (zone === 'background') {
                slide.background = { path: imgPath };
            } else {
                slide.addImage({
                    path: imgPath,
                    x: 6.0, y: 0.5, w: 3.5, h: 4.625,
                    sizing: { type: 'contain', w: 3.5, h: 4.625 },
                    altText: imageData.alt_text || '',
                });
            }
        }
    }

    // --- Speaker notes ---
    if (noteData) {
        slide.addNotes(noteData.text);
    }

    return [slide];
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
    const assetReport = validateImageAssets(imageManifest, DECK_DIR);
    if (assetReport.warnings.length > 0) {
        console.warn('Image asset warnings:');
        assetReport.warnings.forEach(w => console.warn(`  - ${w}`));
    }

    // Create presentation
    const pptx = new PptxGenJS();

    // Set layout dimensions from StyleGuide
    const layoutW = styleGuide.layout?.slide_width_inches || 10;
    const layoutH = styleGuide.layout?.slide_height_inches || 5.625;
    pptx.defineLayout({ name: 'DECK_LAYOUT', width: layoutW, height: layoutH });
    pptx.layout = 'DECK_LAYOUT';

    // Set theme fonts
    pptx.theme = {
        headFontFace: styleGuide.typography.heading_font,
        bodyFontFace: styleGuide.typography.body_font,
    };

    // Register slide masters
    registerSlideMasters(pptx, styleGuide);

    // Build each slide
    for (const slideData of outline.slides) {
        buildSlide(pptx, slideData, styleGuide, imageManifest, chartManifest, speakerNotes);
    }

    // Write output
    const outputDir = path.join(DECK_DIR, 'output');
    fs.mkdirSync(outputDir, { recursive: true });
    const outputPath = path.join(outputDir, 'presentation.pptx');
    await pptx.writeFile({ fileName: outputPath });

    // Report
    const sizeReport = reportFileSize(outputPath);
    console.log(`Deck assembled: ${outputPath}`);
    console.log(`  Slides: ${outline.slides.length}`);
    console.log(`  File size: ${sizeReport.size_human}`);
    console.log(`  Within 100MB limit: ${sizeReport.within_limit}`);

    return { outputPath, sizeReport, assetReport };
}

// Run
assembleDeck().catch(err => {
    console.error('Assembly failed:', err);
    process.exit(1);
});
