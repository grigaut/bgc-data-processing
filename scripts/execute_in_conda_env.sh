#!/bin/bash
SECONDS=0
CONDA_REQUIREMENTS=environment.yml
ASK_EXISTS=false
# Conda environment in order not to rebuild already existing env
CONDA_ENV_PATH="/home/${USER}/.conda/envs"
# Reading first line from $CONDA_REQUIREMENTS to find environment's name
ENV_NAME=$(head -n 1 environment.yml | cut -f2 -d ' ')

if [ -e ${CONDA_ENV_PATH}/${ENV_NAME} ] ; then # if env exists
    # if the environment exists, asking to update it => can be ignored setting ASK_EXISTS to false
    if $ASK_EXISTS ; then
        echo "A environment with the name ${ENV_NAME} exists."
        echo " Do you want to use it ?"
        while true; do
            read -p "  ([Y]/N)  " yn
            case $yn in
                Y|y|"") echo "Updating ${ENV_NAME}"; break;;
                N|n) exit;;
                * ) echo "Please answer yes or no.";;
            esac
        done
    fi
    # update env using .yml file
    $CONDA_EXE env update -q --file $CONDA_REQUIREMENTS
else : # if environment not existing
    echo "Creating environment ${ENV_NAME}"
    # create environment using .yml file
    $CONDA_EXE env create -q --file $CONDA_REQUIREMENTS
fi
echo "Installing packages/modules"
# Package/module install using poetry (-q is to remove poetry outputs)
$CONDA_EXE run --no-capture-output -n $ENV_NAME poetry install -q --without dev.docs
echo "Running Script"
# Python script running using arguments given when executing this script
$CONDA_EXE run --no-capture-output -n $ENV_NAME python $@
echo "Execution time : " $SECONDS " seconds"