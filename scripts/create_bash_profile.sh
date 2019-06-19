#! /bin/bash


# run $source ~/.bash_profile after running this script


FILE=~/.bash_profile

if [ -f "$FILE" ]; then
    echo "$FILE already exists."
else 
    touch ~/.bash_profile
    
    # add convenience functions
    echo "alias ll='ls -FGlAhp'" >> ~/.bash_profile
    echo "alias which='type -all'" >> ~/.bash_profile
    
    # add Ames Stereo Pipeline to path
    echo 'export PATH="~/third-party-tools/asp/StereoPipeline/bin:$PATH"' >> ~/.bash_profile
    
fi
