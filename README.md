# Megascans_Custom_LOD_and_Bake
This tool allows you to generate new LODs and bake out additional maps when working with a Quixel Megascans Asset, imported from Quixel Bridge / Livelink, in Houdini.  This contains a framework I created to easily create and change parameters of nodes, called Big Framework. This also includes helper tools called LOD, and Bake, which abstract creating an LOD and baking textures.

## Installation:

###### STEP 1) Add to your houdini.env file (usually found in C:/Users/Nathan Longhurst/Documents/Houdini18.0/houdini.env):

PYTHONPATH = "path to folder containing these .py files"

When Houdini is launched, it takes note of the variables in its houdini.env . When a shelftool tries to import a python module, it'll look at all of the places it knows to look for Python code, PYTHONPATH is one of these.


###### STEP 2) Add the following code to a new shelf tool:

"
import hdefereval

import megascans_asset
reload(megascans_asset) # optional (in the case you make a change to the code, houdini doesn't use the pre-compiled version of the script it has)

hdefereval.executeDeferred(megascans_asset.main) # hdefereval is something fancy, it runs the function/method passed to it in the main thread (this is necessary because this shelf tool has UI which won't quit out properly unless this tool is run on the main thread)

"

## To use, simply click on a Megascans Asset Subnet (which has been imported in to Houdini via Quixel Bridge), and click on the shelf tool made above.
