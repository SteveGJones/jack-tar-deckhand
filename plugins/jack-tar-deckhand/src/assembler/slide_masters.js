/**
 * Slide master definitions for PptxGenJS.
 *
 * Maps the 12 slide_type values from the SlideOutline schema to
 * PptxGenJS defineSlideMaster() calls. Each master defines background
 * treatment, content zones (text_zone, image_zone), and standard
 * decorative elements.
 *
 * Layout measurements derived from:
 * - research/01-slide-layout-intelligence.md (grid system, content zones)
 * - docs/architecture/data-contracts.md (StyleGuide layout templates)
 *
 * Slide dimensions: 10" x 5.625" (standard 16:9 at 10" width)
 */

const SLIDE_WIDTH = 10;
const SLIDE_HEIGHT = 5.625;
const MARGIN = 0.5;

/**
 * Register all slide masters with the PptxGenJS instance.
 *
 * @param {PptxGenJS} pptx - PptxGenJS instance
 * @param {Object} styleGuide - StyleGuide contract data
 */
function registerSlideMasters(pptx, styleGuide) {
    const palette = styleGuide.palette;
    const typo = styleGuide.typography;

    // Title Slide
    pptx.defineSlideMaster({
        title: 'MASTER_TITLE',
        background: { color: palette.background_alt },
        objects: [
            {
                placeholder: {
                    options: {
                        name: 'title',
                        type: 'title',
                        x: 1.0, y: 1.5, w: 8.0, h: 1.5,
                        fontSize: typo.heading_sizes?.title_slide || 44,
                        fontFace: typo.heading_font,
                        color: palette.text_on_dark || 'FFFFFF',
                        align: 'center',
                        valign: 'bottom',
                    },
                },
            },
            {
                placeholder: {
                    options: {
                        name: 'subtitle',
                        type: 'body',
                        x: 1.5, y: 3.2, w: 7.0, h: 1.0,
                        fontSize: typo.heading_sizes?.subheading || 20,
                        fontFace: typo.body_font,
                        color: palette.text_muted || '718096',
                        align: 'center',
                    },
                },
            },
        ],
    });

    // Section Divider
    pptx.defineSlideMaster({
        title: 'MASTER_SECTION_DIVIDER',
        background: { color: palette.primary },
        objects: [
            {
                placeholder: {
                    options: {
                        name: 'title',
                        type: 'title',
                        x: 1.0, y: 1.8, w: 8.0, h: 1.5,
                        fontSize: typo.heading_sizes?.section_divider || 36,
                        fontFace: typo.heading_font,
                        color: palette.text_on_dark || 'FFFFFF',
                        align: 'center',
                        valign: 'middle',
                    },
                },
            },
        ],
    });

    // Content (standard text + optional image)
    pptx.defineSlideMaster({
        title: 'MASTER_CONTENT',
        background: { color: palette.background },
        objects: [
            {
                placeholder: {
                    options: {
                        name: 'title',
                        type: 'title',
                        x: MARGIN, y: MARGIN, w: 9.0, h: 0.8,
                        fontSize: typo.heading_sizes?.slide_heading || 28,
                        fontFace: typo.heading_font,
                        color: palette.text_primary,
                    },
                },
            },
            {
                placeholder: {
                    options: {
                        name: 'body',
                        type: 'body',
                        x: MARGIN, y: 1.5, w: 5.5, h: 3.625,
                        fontSize: typo.body_size || 16,
                        fontFace: typo.body_font,
                        color: palette.text_primary,
                        lineSpacingMultiple: typo.line_spacing || 1.4,
                    },
                },
            },
        ],
    });

    // Two Column
    pptx.defineSlideMaster({
        title: 'MASTER_TWO_COLUMN',
        background: { color: palette.background },
        objects: [
            {
                placeholder: {
                    options: {
                        name: 'title',
                        type: 'title',
                        x: MARGIN, y: MARGIN, w: 9.0, h: 0.8,
                        fontSize: typo.heading_sizes?.slide_heading || 28,
                        fontFace: typo.heading_font,
                        color: palette.text_primary,
                    },
                },
            },
        ],
    });

    // Image Feature (full-bleed or half-bleed image)
    pptx.defineSlideMaster({
        title: 'MASTER_IMAGE_FEATURE',
        background: { color: palette.background },
    });

    // Data Chart
    pptx.defineSlideMaster({
        title: 'MASTER_DATA_CHART',
        background: { color: palette.background },
        objects: [
            {
                placeholder: {
                    options: {
                        name: 'title',
                        type: 'title',
                        x: MARGIN, y: MARGIN, w: 9.0, h: 0.8,
                        fontSize: typo.heading_sizes?.slide_heading || 28,
                        fontFace: typo.heading_font,
                        color: palette.text_primary,
                    },
                },
            },
        ],
    });

    // Stat Callout (big number)
    pptx.defineSlideMaster({
        title: 'MASTER_STAT_CALLOUT',
        background: { color: palette.background_alt },
    });

    // Quote
    pptx.defineSlideMaster({
        title: 'MASTER_QUOTE',
        background: { color: palette.background_alt },
    });

    // Icon Grid
    pptx.defineSlideMaster({
        title: 'MASTER_ICON_GRID',
        background: { color: palette.background },
        objects: [
            {
                placeholder: {
                    options: {
                        name: 'title',
                        type: 'title',
                        x: MARGIN, y: MARGIN, w: 9.0, h: 0.8,
                        fontSize: typo.heading_sizes?.slide_heading || 28,
                        fontFace: typo.heading_font,
                        color: palette.text_primary,
                    },
                },
            },
        ],
    });

    // Diagram
    pptx.defineSlideMaster({
        title: 'MASTER_DIAGRAM',
        background: { color: palette.background },
        objects: [
            {
                placeholder: {
                    options: {
                        name: 'title',
                        type: 'title',
                        x: MARGIN, y: MARGIN, w: 9.0, h: 0.8,
                        fontSize: typo.heading_sizes?.slide_heading || 28,
                        fontFace: typo.heading_font,
                        color: palette.text_primary,
                    },
                },
            },
        ],
    });

    // Closing / CTA
    pptx.defineSlideMaster({
        title: 'MASTER_CLOSING',
        background: { color: palette.background_alt },
        objects: [
            {
                placeholder: {
                    options: {
                        name: 'title',
                        type: 'title',
                        x: 1.0, y: 1.5, w: 8.0, h: 1.5,
                        fontSize: typo.heading_sizes?.title_slide || 44,
                        fontFace: typo.heading_font,
                        color: palette.text_on_dark || 'FFFFFF',
                        align: 'center',
                        valign: 'middle',
                    },
                },
            },
        ],
    });

    // Blank Visual (breathing room)
    pptx.defineSlideMaster({
        title: 'MASTER_BLANK_VISUAL',
        background: { color: palette.background },
    });
}

/**
 * Map slide_type to master name.
 */
const SLIDE_TYPE_TO_MASTER = {
    'title': 'MASTER_TITLE',
    'section_divider': 'MASTER_SECTION_DIVIDER',
    'content': 'MASTER_CONTENT',
    'two_column': 'MASTER_TWO_COLUMN',
    'image_feature': 'MASTER_IMAGE_FEATURE',
    'data_chart': 'MASTER_DATA_CHART',
    'stat_callout': 'MASTER_STAT_CALLOUT',
    'quote': 'MASTER_QUOTE',
    'icon_grid': 'MASTER_ICON_GRID',
    'diagram': 'MASTER_DIAGRAM',
    'closing': 'MASTER_CLOSING',
    'blank_visual': 'MASTER_BLANK_VISUAL',
};

module.exports = { registerSlideMasters, SLIDE_TYPE_TO_MASTER, SLIDE_WIDTH, SLIDE_HEIGHT, MARGIN };
