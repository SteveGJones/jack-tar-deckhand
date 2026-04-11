"""PowerPoint built-in SmartArt layouts supported by the pptx_native engine.

Each layout module exposes a `build_data_model(extracted_data)` function
that produces the bytes for `ppt/diagrams/data1.xml` from an input data
structure shaped for that layout. Layouts read their own constants
(seed path, layout URI, capacity limits) from the catalog rather than
hardcoding them.

v1 layouts: process1 (this file — currently only process is implemented).
Future layouts added in Phase 4: cycle2, orgChart1, basicTimeline1.
"""
