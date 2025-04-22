# Light-Minded

Light-Minded is an interactive LED and fiber-optic brain sculpture installation. Participants’ inputs and responses to prompts are decoded into keywords that query a large database of neuroimaging studies, lighting up brain areas associated with these inputs to create a dynamic, colorful display of brain activity.

This project is currently being developed by:
Amy Romanello and Zach Dunton

This project was conceptualized by:
Stephan Krohn

## Project structure

Light-minded can be thought of as a set of modules, or components, currently being developed by individual team members. 
As of April 2025, work on the sculpture design and LED infrastructure is driven by Zach Dunton. 
Fullstack software development, including integration with NiMARE tools and neuroimaging datasets, is carried out by Amy Romanello. 
Stephan Krohn provides ongoing consultations on design and functionality. 

Questions? <amy.romanello@nothingtwoserious.art>

## Viewing the Regions in the Atlas

Included in this repo is a viewer to view the current regions, and turn them on and off.

Run `simulator.py` to generate the web files, then use a simple webserver to view the [result on localhost](http://localhost:8000/web/brain_regions_3d.html)
```bash
python scripts/simulator.py
python -m http.server 8000
```

## Features

* TODO

## Credits

* Free software: MIT license




