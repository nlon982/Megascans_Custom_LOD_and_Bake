# Megascans_Custom_LOD_and_Bake
This tool allows you to generate new LODs and bake out additional maps when working with a Quixel Megascans Asset that has been imported with Quixel Bridge / Livelink, in Houdini.

![image](https://user-images.githubusercontent.com/69462081/110022718-263a0a80-7d91-11eb-8ed9-25c0c2953734.png)

This contains a framework I created to easily create and change parameters of nodes (it's a language which encodes information to create nodes and change parameters of nodes, in a string - which can then be executed whenever you like), called Big Framework (a simpler version is here: https://github.com/nlon982/BigFramework). This also includes helper tools called LOD, and Bake, which abstract creating an LOD and baking textures.

### 11/01/2021: This tool works completely, to my knowledge. Previously there was a mistake in the code which meant it didn't work for Megascans Assets that were imported for anything other than Redshift (e.g. Mantra), so I'm happy that's sorted. It also works with both Python 2 and Python 3 versions of Houdini (I tested on 18.5.351, but I have no reason to think it wouldn't work on any other version).

### To use, simply click on a Megascans Asset Subnet (which has been imported in to Houdini via Quixel Bridge), and click on the shelf tool made by the installation process below.

See https://www.byccollective.com/blog-posts/houdini-megascans-custom-lod-and-baking-tool for a video tutorial of its use and installation. Particularly, see 5:50 for the tool being used. The entire video is great for an explanation of what's happening.

## Installation:

#### STEP 1) Add the following to your houdini.env file (usually found somewhere like C:/Users/Nathan Longhurst/Documents/Houdini18.0/houdini.env, note: make sure you're in the correct Houdini directory e.g. if you're using Houdini 17.5, then look for a folder called 'Houdini17.5'):

```
PYTHONPATH = "path to folder containing the .py files downloaded from this GitHub"
```

###### Why do I have to do this? 
The shelftool below tries to import the Python files ("modules") you just downloaded. Houdini has a list of places that it can look for Python files, and it's just a matter of making sure that one of the places Houdini looks for Python files is the folder containing *these* Python files. Fun fact: when Houdini is launched, it looks at the variables in its houdini.env, and the value corresponding with the variable 'PYTHONPATH' is one of these places Houdini will look for Python code.

All the code could be made to work in a single script (and therefore all of it would only need to be placed in the shelf tool, and this would be a one step installation process). From a development point of view, it's much easier to not have all the code contained in the shelftool - so I haven't done this - however, maybe this is a 'special release' that should be made so that installation is one step.

#### STEP 2) Add the following code to a new shelf tool:

```
import hdefereval

import megascans_asset
import reload_helper

reload_helper.foolproof_reload(megascans_asset) # optional (in the case you make a change to the code, this will make sure houdini doesn't use the pre-compiled version of the script it has)


hdefereval.executeDeferred(megascans_asset.main) # hdefereval is something fancy, it runs the function/method passed to it in the main thread (this is necessary because this shelf tool has UI which won't quit out properly unless this tool is run on the main thread)

```


