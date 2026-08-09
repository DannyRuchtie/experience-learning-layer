# Experience Learning Layer

**From episodes to revisable concepts: an open research specification for
evidence-grounded learning in language agents.**

The Experience Learning Layer (ELL) asks what must happen between remembering
an event and earning a reusable concept: preserve exact evidence, propose an
interpretation, test its scope, apply it later, and revise it when outcomes or
counterexamples disagree.

![Where the Experience Learning Layer sits](chapters/assets/diagrams/ell-overview.svg)

## Read and edit the paper

[`index.qmd`](index.qmd) and the files in [`chapters/`](chapters/) are the paper.
They are ordinary Quarto Markdown files and are the only canonical source. Edit
a chapter, render the project, and both the navigable website and downloadable
PDF are rebuilt from the same text.

The published website will be available through GitHub Pages after the pull
request is merged and the publishing workflow runs on `main`.

## Local preview

Install [Quarto](https://quarto.org/docs/get-started/) and its TinyTeX PDF engine,
then run:

```bash
quarto preview
```

To build the complete website and PDF without starting the preview server:

```bash
quarto render
```

Generated files are written to `_book/` and are intentionally ignored by Git.

## Repository structure

| Path | Purpose |
|---|---|
| `index.qmd` | Abstract and publication status |
| `chapters/` | Editable paper chapters |
| `chapters/assets/diagrams/` | Shared web and print diagrams |
| `examples/` | Synthetic lifecycle examples referenced by the paper |
| `_quarto.yml` | Contents, metadata, website, and PDF configuration |
| `styles.css` | Small visual layer for the HTML edition |
| `.github/workflows/publish.yml` | Automatic GitHub Pages publication |

There is intentionally no application, server, database, provider SDK, or
learning kernel in this repository. The interfaces and algorithms in the paper
remain research specifications until an evaluated implementation exists.

## License

The paper, diagrams, examples, and publishing configuration are available under
the [MIT License](LICENSE).
