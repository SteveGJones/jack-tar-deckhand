#!/bin/bash
# Convert a .pptx to PDF using PowerPoint Mac via AppleScript.
#
# Unlike LibreOffice headless, this produces pixel-perfect SmartArt
# rendering because PowerPoint runs its native layout algorithm and
# regenerates the drawing cache before exporting.
#
# Usage:
#   tools/pptx_to_pdf.sh input.pptx [output.pdf]
#
# If output.pdf is not specified, uses input stem + .pdf in the same dir.
#
# Requirements:
#   - Microsoft PowerPoint for Mac installed
#   - macOS (uses osascript / AppleScript)
#   - On first run, macOS will prompt to grant automation permissions
#     for Terminal/Claude Code to control PowerPoint. Accept the
#     prompt — this is a one-time system permission grant stored in
#     System Preferences → Privacy & Security → Automation.
#
# Key insight (discovered during spike 6b, 2026-04-09):
# PowerPoint must SAVE the .pptx first (triggering drawing cache
# regeneration) before the PDF export will work. Without the save
# step, export fails with error -9074 because the SmartArt layout
# hasn't been computed yet.

set -euo pipefail

INPUT="${1:?Usage: pptx_to_pdf.sh input.pptx [output.pdf]}"
INPUT_ABS="$(cd "$(dirname "$INPUT")" && pwd)/$(basename "$INPUT")"

if [ ! -f "$INPUT_ABS" ]; then
    echo "Error: file not found: $INPUT_ABS" >&2
    exit 1
fi

if [ -n "${2:-}" ]; then
    OUTPUT_ABS="$(cd "$(dirname "$2")" 2>/dev/null && pwd)/$(basename "$2")" 2>/dev/null || OUTPUT_ABS="$2"
else
    OUTPUT_ABS="${INPUT_ABS%.pptx}.pdf"
    OUTPUT_ABS="${OUTPUT_ABS%.pptm}.pdf"
fi

echo "Converting: $INPUT_ABS"
echo "Output:     $OUTPUT_ABS"

osascript << APPLEOF
tell application "Microsoft PowerPoint"
    activate
    open POSIX file "$INPUT_ABS"
    delay 5
    set p to active presentation
    -- Save first to trigger drawing cache regeneration for SmartArt
    save p
    delay 2
    -- Export as PDF
    save p in ((POSIX file "$OUTPUT_ABS") as text) as save as PDF
    delay 2
    close p saving no
end tell
APPLEOF

if [ -f "$OUTPUT_ABS" ]; then
    echo "Success: $(ls -la "$OUTPUT_ABS")"
else
    echo "Error: PDF not produced" >&2
    exit 1
fi
