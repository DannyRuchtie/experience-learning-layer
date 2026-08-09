# Paper source and publication builds

`ELL_Paper.md` is the canonical living manuscript. The publication commands derive
three reader-facing formats from that source and the shared definitions in
`diagrams.py`:

- `python3 -m paper.build_paper` writes the current PDF to `output/pdf/`;
- `python3 -m paper.build_html` writes the multi-page reading edition to `docs/`;
- `python3 -m paper.verify_publication` checks links, page navigation, diagrams,
  HTML structure, expected paper sections, and byte-for-byte agreement with a clean
  rebuild.

Use `make paper` to rebuild every publication artifact, then `make check` before
publishing. Generated HTML, CSS, SVG diagrams, and the current PDF are tracked so a
reader can use the repository without installing its build environment.

The builders are deterministic. A clean rebuild must not change the generated files;
the verification command fails if the committed HTML, CSS, SVG, or PDF has drifted
from the Markdown manuscript and shared diagram definitions.

The archived v0.1 PDF remains under `paper/archive/` for historical comparison.
