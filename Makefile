# NeMo Gym — top-level convenience targets.
# Fern-related targets live here so contributors don't have to remember the
# exact `cd fern && npx … fern-api` invocations. CI workflows under
# `.github/workflows/fern-docs-*.yml` are the source of truth for the
# published pipeline; these targets just mirror the local-developer entry
# points. For Sphinx (legacy) docs, see `docs/Makefile`.

FERN_DIR := fern
PUBLISH_WORKFLOW := Publish Fern Docs

.DEFAULT_GOAL := help

.PHONY: help fern-dev fern-check fern-preview fern-publish fern-generate-library

help:
	@echo ""
	@echo "NeMo Gym top-level Make targets"
	@echo "==============================="
	@echo ""
	@echo "  make fern-dev               Generate the library reference and start the Fern dev server"
	@echo "  make fern-check             Validate Fern docs config ('fern check' via npm run check)"
	@echo "  make fern-preview           Build a shared preview URL on *.docs.buildwithfern.com (needs DOCS_FERN_TOKEN)"
	@echo "  make fern-publish           Trigger the 'Publish Fern Docs' workflow on origin/main"
	@echo "  make fern-generate-library  Regenerate the autodoc library reference under fern/product-docs/"
	@echo ""
	@echo "For Sphinx (legacy) docs targets, see docs/Makefile."
	@echo ""

# Local-only preview. `fern docs md generate` populates fern/product-docs/ from
# the nemo_gym package source (declared under `libraries:` in fern/docs.yml);
# `fern docs dev` then serves the site on localhost:3000. Re-run `make fern-dev`
# only when the library source changes — for prose-only iteration,
# `cd fern && npx -y fern-api@latest docs dev` alone is enough after the first
# generate.
fern-dev: fern-generate-library
	cd $(FERN_DIR) && npx -y fern-api@latest docs dev

fern-check:
	cd $(FERN_DIR) && npm run check

fern-generate-library:
	cd $(FERN_DIR) && npx -y fern-api@latest docs md generate

# Shared preview hosted at <repo-slug>.docs.buildwithfern.com — useful for
# sharing a work-in-progress link before merge. Requires DOCS_FERN_TOKEN in the
# environment (org secret of the same name is wired into CI).
fern-preview:
	cd $(FERN_DIR) && npx -y fern-api@latest generate --docs --preview

# Trigger the Publish Fern Docs workflow on origin/main via workflow_dispatch.
# Alternative: tag a release with `git tag docs/v0.3.0 && git push origin docs/v0.3.0`
# — the workflow also fires on `docs/v*` tag pushes.
fern-publish:
	gh workflow run "$(PUBLISH_WORKFLOW)" --ref main
