/**
 * Progressive Build Generation for PptxGenJS.
 *
 * Simulates animations by generating multiple slides where each
 * successive slide adds one more element. Covers ~80% of animation
 * use cases presenters actually need (Research #14).
 *
 * Triggered when a slide's speaker notes contain a 'build_animation'
 * cue from the SpeakerNotes contract.
 */

const { MARGIN } = require('./slide_masters');

/**
 * Determine if a slide should use progressive builds.
 *
 * @param {Object} slideData - Slide definition from SlideOutline
 * @param {Object} noteData - Speaker note for this slide (may be null)
 * @returns {boolean}
 */
function shouldProgressiveBuild(slideData, noteData) {
    if (!noteData || !noteData.cues) return false;
    return noteData.cues.some(cue => cue.type === 'build_animation');
}

/**
 * Generate progressive build slides for a bullet-point slide.
 *
 * Creates N slides (one per bullet) where each slide shows all
 * bullets up to that point. Previous bullets are dimmed.
 *
 * @param {PptxGenJS} pptx - PptxGenJS instance
 * @param {Object} slideData - Slide definition from SlideOutline
 * @param {Object} styleGuide - StyleGuide contract
 * @param {string} masterName - Master slide name
 * @param {Object} noteData - Speaker note (optional)
 * @returns {Array} Array of created slides
 */
function generateBulletBuild(pptx, slideData, styleGuide, masterName, noteData) {
    const bullets = slideData.body_points || [];
    if (bullets.length === 0) return [];

    const palette = styleGuide.palette;
    const typo = styleGuide.typography;
    const slides = [];

    for (let step = 1; step <= bullets.length; step++) {
        const slide = pptx.addSlide({ masterName });

        // Add title (always visible)
        slide.addText(slideData.headline, {
            x: MARGIN, y: MARGIN, w: 9.0, h: 0.8,
            fontSize: typo.heading_sizes?.slide_heading || 28,
            fontFace: typo.heading_font,
            color: palette.text_primary,
            bold: true,
        });

        // Add bullets up to current step
        for (let i = 0; i < step; i++) {
            const isCurrent = i === step - 1;
            slide.addText(bullets[i], {
                x: MARGIN + 0.3, y: 1.5 + (i * 0.7), w: 8.5, h: 0.6,
                fontSize: typo.body_size || 16,
                fontFace: typo.body_font,
                color: isCurrent ? palette.text_primary : palette.text_muted,
                bullet: true,
                lineSpacingMultiple: typo.line_spacing || 1.4,
            });
        }

        // Add speaker notes only on the final build step
        if (step === bullets.length && noteData) {
            slide.addNotes(noteData.text);
        }

        slides.push(slide);
    }

    return slides;
}

module.exports = { shouldProgressiveBuild, generateBulletBuild };
