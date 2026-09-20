---
tags:
  - node/theme
---

# Graph Views

Open Obsidian's global Graph view and paste one of these expressions into **Filters → Search files**. Search filters select files in the graph; they do not create relationships. See [Obsidian's Graph view documentation](https://help.obsidian.md/plugins/graph).

| View | Filter | Purpose |
| --- | --- | --- |
| First relationship cluster | `path:"Concepts/" tag:#cluster/rates-and-bonds` | Eight concepts with reviewed relationship statements; configured as the graph's initial filter. |
| All concepts | `path:"Concepts/"` | Direct concept links, including the remaining unfinished concepts. Enable Orphans to inspect disconnected concepts. |
| Sources and concepts | `path:"Transcripts/" OR path:"Concepts/"` | Inspect source coverage and concept mentions without navigation hubs. |
| Full library | Clear the filter | Include navigation pages, concepts and transcripts. |

An arrow in Obsidian means that one note links to another. It does not mean causation, agreement or evidence strength. Read the labeled relationship in the concept note for its meaning. Repeated mentions within one transcript do not create additional distinct node pairs.

Topic pages are navigation; their classification links should be excluded when measuring semantic concept connectivity. A source link supports attribution to a speaker, while an official reference supports the stated definition or mechanism within its scope.

Start with [[Topics/Interest Rates Inflation and Bonds|Interest Rates, Inflation and Bonds]], or return to [[Topics/Index|Knowledge Map]].
