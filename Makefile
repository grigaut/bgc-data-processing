.ONESHELL:
	SHELL:=/bin/bash
.PHONY: create-env install update run-save run-plot documentation docs-build clean-dirs

ENVIRONMENT_FILEPATH = environment.yml
SAVE_SCRIPT_PATH = scripts/save_data.py
PLOT_SCRIPT_PATH = scripts/plot_mesh.py
OUTPUT_DIRS = bgc_data bgc_figs
VENV := ./.venv
POETRY := $(VENV)/bin/poetry
PYTHON := $(VENV)/bin/python3.11
MKDOCS := $(VENV)/bin/mkdocs
PRECOMMIT := $(VENV)/bin/pre-commit
HOOKS := ./.git/hooks

default:
	@echo "Call a specific subcommand: create-env,install,update,documentation"

all:
	@$(MAKE) -s install
	@$(MAKE) -s pre-commit

clean:
	rm -r -f $(VENV)
	rm -r -f $(HOOKS)

$(VENV): $(CONDA_EXE) $(ENVIRONMENT_FILEPATH)
	@$(MAKE) -s clean
	$(CONDA_EXE) env create -q --file $(ENVIRONMENT_FILEPATH) --prefix $(VENV)

.PHONY: clean-dirs
clean-dirs:
	$(foreach dir, $(OUTPUT_DIRS), rm -r -f $(dir))

.PHONY: create-env
create-env:
	@$(MAKE) -s $(VENV)

.PHONY: install
install: poetry.lock
	@$(MAKE) -s $(VENV)
	$(POETRY) install

.PHONY: update
update:
	@$(MAKE) -s $(VENV)
	$(POETRY) update

.PHONY: run-save
run-save:
	@$(MAKE) -s $(VENV)
	$(POETRY) install --without dev,docs
	$(PYTHON) $(SAVE_SCRIPT_PATH)

.PHONY: run-plot
run-plot:
	@$(MAKE) -s $(VENV)
	$(POETRY) install --without dev,docs
	$(PYTHON) $(PLOT_SCRIPT_PATH)

.PHONY: view-docs
view-docs:
	@$(MAKE) -s $(VENV)
	$(POETRY) install --only docs
	$(MKDOCS) serve

./site:
	@$(MAKE) -s $(VENV)
	$(POETRY) install --only docs
	$(MKDOCS) build

.PHONY: build-docs
build-docs:
	@$(MAKE) -s ./site

pre-commit: $(PRECOMMIT)
	$(PRECOMMIT) install
