# Living paper

`ELL_Paper.md` is the canonical, editable manuscript. It retains the full v0.1
research proposal and adds dated revisions as the architecture, implementation,
evaluation, and results evolve.

Build the current PDF from the repository root:

```bash
make paper
```

The stable output is
`output/pdf/Experience-Learning-Layer-Paper-current.pdf`. The checked-in
`archive/Experience-Learning-Layer-Paper-v0.1.pdf` is the immutable original
published draft and should never be overwritten. New empirical claims must include
their experiment configuration and evidence; implementation status must identify
the exact verified scope and distinguish deferred release gates.

The builder uses ReportLab and generates an A4 paper with bookmarks, a table of
contents, page numbering, and Unicode-capable bundled fonts. Update the Markdown,
run `make paper`, inspect the rendered pages, and commit source and output together.
