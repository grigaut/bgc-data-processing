#!/bin/bash
echo "Do you want to [B]uild the documentation HTML files or to [D]isplay documnetation ?"
while true; do
    read -p "  (B/[D])  " yn
    case $yn in
        B|b) make docs-build; break;;
        D|d|"") make documentation; break;;
        * ) echo "Please answer B (Building docs) or D (Displaying docs).";;
    esac
done