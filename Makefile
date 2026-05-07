.DEFAULT_GOAL := help

.PHONY: help fern-dev fern-check fern-generate-library

help: ## Show this help message
	@echo ""
	@echo "NeMo Gym top-level Make targets"
	@echo "==============================="
	@echo ""
	@echo "  make fern-dev               Generate the library reference and start the Fern dev server"
	@echo "  make fern-check             Validate Fern docs config (fern check)"
	@echo "  make fern-generate-library  Regenerate the autodoc library reference under fern/product-docs/"
	@echo ""
	@echo "For Sphinx (legacy) docs targets, see docs/Makefile."
	@echo ""

fern-generate-library:
	cd fern && npx -y fern-api@latest docs md generate

fern-check:
	cd fern && npm run check

fern-dev: fern-generate-library
	cd fern && npx -y fern-api@latest docs dev
