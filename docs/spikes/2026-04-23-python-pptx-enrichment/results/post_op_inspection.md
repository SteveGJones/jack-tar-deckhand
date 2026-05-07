# OOXML post-op inspection — all_ops.pptx

## Slide 1 — background image (Op1)

`<p:cSld>/<p:bg>` present and well-formed:

```xml
<p:bg>
  <p:bgPr>
    <a:blipFill dpi="0" rotWithShape="1">
      <a:blip r:embed="rId3"/>
      <a:srcRect/>
      <a:stretch><a:fillRect/></a:stretch>
    </a:blipFill>
    <a:effectLst/>
  </p:bgPr>
</p:bg>
```

`slide1.xml.rels` contains the image relationship:

```xml
<Relationship Id="rId3" Type=".../relationships/image" Target="../media/image1.png"/>
```

## Slide 4 — SmartArt graphicFrame (Op3)

Exactly one `<p:graphicFrame>` with `<dgm:relIds>` pointing at all four diagram parts:

```xml
<dgm:relIds r:dm="rId3" r:lo="rId4" r:qs="rId5" r:cs="rId6"/>
```

`slide4.xml.rels` contains all four diagram relationships:

```xml
<Relationship Id="rId3" Type=".../diagramData"      Target="../diagrams/data1.xml"/>
<Relationship Id="rId4" Type=".../diagramLayout"    Target="../diagrams/layout1.xml"/>
<Relationship Id="rId5" Type=".../diagramQuickStyle" Target="../diagrams/quickStyle1.xml"/>
<Relationship Id="rId6" Type=".../diagramColors"    Target="../diagrams/colors1.xml"/>
```

## Slide 2 — embedded picture (Op2)

Not XML-inspected here but verified by test (MSO_SHAPE_TYPE.PICTURE at captured geometry) and by visual review (picture visible in PowerPoint PDF export).

## Package-level observations

- `ppt/media/image1.png` present (single image part — python-pptx deduplicated op1's and op2's use of placeholder.png by sha1, which is correct behaviour).
- `ppt/diagrams/{data1,layout1,quickStyle1,colors1}.xml` all present.
- Slide masters and layouts preserved 1:1 from seed (slideMaster1.xml + slideLayout1.xml — PptxGenJS only generates one of each).
- Theme preserved (theme1.xml — 8397 bytes → 8397 bytes, identical).
- Content Types registration correct (checked implicitly by successful python-pptx round-trip).

## File size change — investigated

Seed: 157,465 bytes. All_ops: 56,846 bytes. The size drop is not data loss — it is:
- python-pptx serialises zips without empty directory entries (PptxGenJS includes them)
- python-pptx uses tighter zip deflation defaults
- PptxGenJS embeds some unused parts (e.g. charts/, embeddings/ directory placeholders) that python-pptx drops if empty

Content was compared: all slide XML files, both masters, the layout, the theme, and all media are present and non-empty. The PowerPoint Mac gate confirms the file opens and renders correctly, which is the authoritative round-trip test.

## Anomalies / concerns

**Cosmetic (non-blocking):** On slide 4, faint fragments of body text remain visible BEHIND the injected SmartArt. These are elements that were neighbours of the SMARTART marker shape — they were NOT part of the marker itself but lived in other text boxes. The injection only removes the named marker shape; it does not clear surrounding content. For the real bridge, the enrichment step must decide whether to clear marker-adjacent text as part of the operation, or leave that decision to the author of the brief (which could specify that marker-replaced slides should contain only the marker + title).

No other anomalies.
