/**
 * File optimisation for assembled .pptx files.
 *
 * Capabilities:
 * - Image asset validation before embedding
 * - File size reporting and limit checking
 *
 * Corresponds to the assembly-file-optimisation capability in the
 * service catalogue (capability of deck-assembler).
 */

const fs = require('fs');
const path = require('path');

/**
 * Get file size in human-readable format.
 */
function formatSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * Report file size of the assembled .pptx.
 *
 * @param {string} pptxPath - Path to the .pptx file
 * @returns {Object} Size report
 */
function reportFileSize(pptxPath) {
    const stats = fs.statSync(pptxPath);
    return {
        path: pptxPath,
        size_bytes: stats.size,
        size_human: formatSize(stats.size),
        within_limit: stats.size < 100 * 1024 * 1024, // 100MB conference limit
    };
}

/**
 * Validate that all image files referenced in the manifest exist and
 * have reasonable file sizes.
 *
 * @param {Object} imageManifest - ImageManifest contract
 * @param {string} deckDir - DeckContext directory path
 * @returns {Object} Validation result with warnings
 */
function validateImageAssets(imageManifest, deckDir) {
    const warnings = [];
    let totalImageSize = 0;

    for (const img of imageManifest.images || []) {
        const imgPath = path.resolve(deckDir, img.file_path.replace('./tmp/deck/', ''));
        if (!fs.existsSync(imgPath)) {
            warnings.push(`Missing image: ${img.file_path} (${img.image_id})`);
            continue;
        }
        const size = fs.statSync(imgPath).size;
        totalImageSize += size;
        if (size > 10 * 1024 * 1024) {
            warnings.push(`Large image: ${img.image_id} is ${formatSize(size)}`);
        }
    }

    return {
        total_image_size: totalImageSize,
        total_image_size_human: formatSize(totalImageSize),
        warnings,
    };
}

module.exports = { reportFileSize, validateImageAssets, formatSize };
