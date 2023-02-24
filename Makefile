.ONESHELL:
	SHELL:=/bin/bash
.PHONY: create-env install update run-save run-plot documentation docs-build clean-dirs

ENVIRONMENT_FILEPATH = environment.yml
SAVE_SCRIPT_PATH = scripts/save_data.py
PLOT_SCRIPT_PATH = scripts/plot_mesh.py
OUTPUT_DIRS = bgc_data bgc_figs
ENV_PREFIX = ./.venv
RUN_IN_ENV = $(CONDA_EXE) run --no-capture-output -p $(ENV_PREFIX)

default:
	@echo "Call a specific subcommand: create-env,install,update,documentation"

all:
	@$(MAKE) -s install
	
.venv: $(ENVIRONMENT_FILEPATH) poetry.lock
	@$(MAKE) -s clean
	$(CONDA_EXE) env create -q --file $(ENVIRONMENT_FILEPATH) --prefix $(ENV_PREFIX)

clean:
	rm -r -f $(ENV_PREFIX)

clean-dirs:
	$(foreach dir, $(OUTPUT_DIRS), rm -r -f $(dir))

create-env: 
	@$(MAKE) -s .venv

install: 
	@$(MAKE) -s .venv
	$(RUN_IN_ENV) poetry install


update: 
	@$(MAKE) -s .venv
	$(RUN_IN_ENV) poetry update
	$(RUN_IN_ENV) poetry lock
	@$(MAKE) -s .venv

run-save: 
	@$(MAKE) -s .venv
	$(RUN_IN_ENV) poetry install --without dev,docs
	$(RUN_IN_ENV) python $(SAVE_SCRIPT_PATH)

run-plot:
	@$(MAKE) -s .venv
	$(RUN_IN_ENV) poetry install --without dev,docs
	$(RUN_IN_ENV) python $(PLOT_SCRIPT_PATH)

documentation: 
	@$(MAKE) -s .venv
	$(RUN_IN_ENV) poetry install --only docs
	$(RUN_IN_ENV) mkdocs serve

./site: 
	@$(MAKE) -s .venv
	$(RUN_IN_ENV) poetry install --only docs
	$(RUN_IN_ENV) mkdocs build

docs-build:
	@$(MAKE) -s ./site
