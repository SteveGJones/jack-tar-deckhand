# jack-tar-superpower-bridge

*Interim — this stub will be expanded when the bridge plugin is fully
released. See [GitHub issue
#53](https://github.com/SteveGJones/jack-tar-deckhand/issues/53).*

The Superpower Bridge plugin connects the upstream `/pptx` skill to the
Jack-Tar engine plugins (cloud/ollama image generation, SmartArt). It
is the **default route** for new Jack-Tar users — collaborate with
`/pptx` from the start, or rescue a stale `/pptx` deck with a
review-first enrichment pass.

## Skills

| Skill | Purpose |
|-------|---------|
| `/bridge-brief` | Plan a talk and produce a brief that drives `/pptx`. |
| `/enrich-deck`  | Review-first enrichment of an existing `.pptx` — assess what's salvageable, collaborate with the speaker on enrich-in-place vs rebuild. |

## See also — Direct route

If you want the full Jack-Tar pipeline from a brief — brand profile,
narrative architect, strategy map, full QA — without `/pptx`
involvement, use the **deck-conductor** in the
`jack-tar-deckhand` plugin. See
`plugins/jack-tar-deckhand/CLAUDE.md` and the "Choosing your route"
section of the top-level `README.md`.
