UV ?= uv
MOONSHOT_DATA_TAG = 0.7.6
VENDOR = moonshot/.vendor/moonshot-data

.PHONY: vendor suite unit test test-full brief

vendor:  ## clone moonshot-data at the pinned tag (framework modules + built-in recipe)
	@test -d $(VENDOR) || git clone -q --depth 1 --branch $(MOONSHOT_DATA_TAG) \
		https://github.com/aiverify-foundation/moonshot-data.git $(VENDOR)

suite:  ## regenerate Moonshot datasets/recipes/cookbooks from moonshot/cases
	$(UV) run python -m scripts.build_suite

unit:  ## offline unit tests, no API key needed
	$(UV) run pytest -q

test: vendor  ## 40-case sample suite against Gemini, then the brief
	$(UV) run python -m scripts.run_suite --suite sample
	$(UV) run python -m scripts.brief moonshot/.runs/latest.json

test-full: vendor  ## full 150-case suite, plus the unguarded comparison
	$(UV) run python -m scripts.run_suite --suite full --unguarded
	$(UV) run python -m scripts.brief moonshot/.runs/latest.json
