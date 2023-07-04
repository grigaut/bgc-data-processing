.ONESHELL:
	SHELL:=/bin/bash
.PHONY: create-env install update run-save run-plot documentation docs-build clean-dirs

ENVIRONMENT_FILEPATH := environment.yml
OUTPUT_DIRS := bgc_data bgc_figs
SCRIPTS_DIR := scripts
CONFIG_DIR := config
CONFIG_DEFAULT_DIR := config/default
VENV := ./.venv
BIN := $(VENV)/bin/
HOOKS := ./.git/hooks

default:
	@echo "Call a specific subcommand: create-env,install,update,documentation"

# Main Rules

all:
	$(MAKE) -s copy-default-config
	$(MAKE) -s install

clean:
	rm -r -f $(VENV)
	rm -r -f $(HOOKS)

.PHONY: clean-dirs
clean-dirs:
	$(foreach dir, $(OUTPUT_DIRS), rm -r -f $(dir))

$(VENV): $(CONDA_EXE) $(ENVIRONMENT_FILEPATH)
	$(MAKE) -s clean
	$(CONDA_EXE) env create -q --file $(ENVIRONMENT_FILEPATH) --prefix $(VENV)

.PHONY: create-env
create-env:
	$(MAKE) -s $(VENV)

.PHONY: poetry-install
poetry-install: poetry.lock
	$(BIN)poetry install --only main


.PHONY: install
install: poetry.lock
	$(MAKE) -s create-env
	$(MAKE) -s poetry-install

$(CONFIG_DIR)/%.toml: $(CONFIG_DEFAULT_DIR)/%.toml
	echo "Copy $(CONFIG_DEFAULT_DIR)/$*.toml to $(CONFIG_DIR)/$*.toml";\
	cp $(CONFIG_DEFAULT_DIR)/$*.toml $(CONFIG_DIR)/$*.toml
	@echo "# CONFIGURATION FILE COPIED FROM DEFAULT: $(CONFIG_DEFAULT_DIR)/$*.toml\n" | cat - $(CONFIG_DIR)/$*.toml | sed '1s/^#.*$$/&/' > $(CONFIG_DIR)/$*.toml.tmp
	@mv $(CONFIG_DIR)/$*.toml.tmp $(CONFIG_DIR)/$*.toml

.PHONY: copy-default-config
copy-default-config: $(CONFIG_DIR) $(CONFIG_DEFAULT_DIR)
	@for name in $(CONFIG_DEFAULT_DIR)/*.toml ; do\
		$(MAKE) -s $(CONFIG_DIR)/$$(basename $${name});\
	done

.PHONY: run-%
run-%:
	@echo "Executing $(SCRIPTS_DIR)/$(subst -,_,$*).py"
	$(MAKE) -s install
	$(MAKE) -s copy-default-config
	$(BIN)python3.11 $(SCRIPTS_DIR)/$(subst -,_,$*).py

# Documentation Rules

.PHONY: poetry-install-docs
poetry-install-docs: poetry.lock
	$(BIN)poetry install --only docs


.PHONY: install-docs
install-docs:
	$(MAKE) -s create-env
	$(MAKE) -s poetry-install-docs

.PHONY: view-docs
view-docs:
	$(MAKE) -s install-docs
	$(BIN)mkdocs serve

./site:
	$(MAKE) -s install-docs
	$(BIN)mkdocs build

.PHONY: build-docs
build-docs:
	$(MAKE) -s ./site

.PHONY: deploy-docs
deploy-docs:
	$(MAKE) -s install-docs
	$(BIN)mkdocs gh-deploy
	rm -r -f ./site

# Development Rules

.PHONY: poetry-install-dev
poetry-install-dev: poetry.lock
	$(BIN)poetry install

.PHONY: hooks
hooks: $(BIN)pre-commit
	$(BIN)pre-commit install

.PHONY: install-dev
install-dev: poetry.lock
	$(MAKE) -s create-env
	$(MAKE) -s poetry-install-dev
	$(MAKE) -s hooks
