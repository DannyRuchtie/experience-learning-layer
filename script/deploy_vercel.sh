#!/usr/bin/env bash

set -euo pipefail

ELL_QUARTO_BIN="${ELL_QUARTO_BIN:-quarto}"
ELL_VERCEL_BIN="${ELL_VERCEL_BIN:-vercel}"
ELL_VERCEL_PROJECT="${ELL_VERCEL_PROJECT:-experience-learning-layer}"
ELL_VERCEL_SCOPE="${ELL_VERCEL_SCOPE:-dannyruchties-projects}"

if ! command -v "$ELL_QUARTO_BIN" >/dev/null 2>&1; then
  echo "Quarto is required to render the publication." >&2
  exit 1
fi

if ! command -v "$ELL_VERCEL_BIN" >/dev/null 2>&1; then
  echo "Vercel CLI is required to publish the rendered output." >&2
  exit 1
fi

"$ELL_QUARTO_BIN" render

for ELL_REQUIRED_OUTPUT in \
  _book/index.html \
  _book/experience-learning-layer.pdf \
  _book/chapters/01-introduction.html \
  _book/site_libs/quarto-nav/quarto-nav.js
do
  if [[ ! -s "$ELL_REQUIRED_OUTPUT" ]]; then
    echo "Required publication output is missing: $ELL_REQUIRED_OUTPUT" >&2
    exit 1
  fi
done

ELL_RELEASE_DIRECTORY="$(mktemp -d /private/tmp/ell-vercel-release.XXXXXX)"

cleanup_release_directory() {
  case "$ELL_RELEASE_DIRECTORY" in
    /private/tmp/ell-vercel-release.*)
      rm -rf -- "$ELL_RELEASE_DIRECTORY"
      ;;
    *)
      echo "Refusing to remove unexpected release directory: $ELL_RELEASE_DIRECTORY" >&2
      ;;
  esac
}

trap cleanup_release_directory EXIT
cp -R _book/. "$ELL_RELEASE_DIRECTORY/"

(
  cd "$ELL_RELEASE_DIRECTORY"
  "$ELL_VERCEL_BIN" deploy . \
    --prod \
    --yes \
    --project "$ELL_VERCEL_PROJECT" \
    --scope "$ELL_VERCEL_SCOPE"
)
