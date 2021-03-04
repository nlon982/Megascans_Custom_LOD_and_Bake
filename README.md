# Megascans_Custom_LOD_and_Bake
This tool allows you to generate new LODs and bake out additional maps when working with a Quixel Megascans Asset that has been imported with Quixel Bridge / Livelink, in Houdini.

![image](https://user-images.githubusercontent.com/69462081/110022718-263a0a80-7d91-11eb-8ed9-25c0c2953734.png)

This contains a framework I created to easily create and change parameters of nodes (it's a language which encodes information to create nodes and change parameters of nodes, in a string - which can then be executed whenever you like), called Big Framework (a simpler version is here: https://github.com/nlon982/BigFramework). This also includes helper tools called LOD, and Bake, which abstract creating an LOD and baking textures.

### To use, simply click on a Megascans Asset Subnet (which has been imported in to Houdini via Quixel Bridge), and click on the shelf tool made below.

See https://www.byccollective.com/blog-posts/houdini-megascans-custom-lod-and-baking-tool for a video tutorial of its use and installation. Particularly, see 5:50 for the tool being used. The entire video is great for an explanation of what's happening.

## Installation:

#### STEP 1) Add to your houdini.env file (usually found in C:/Users/Nathan Longhurst/Documents/Houdini18.0/houdini.env):

> PYTHONPATH = "path to folder containing the .py files downloaded from this GitHub"

When Houdini is launched, it takes note of the variables in its houdini.env . When a shelftool tries to import a python module (like what the shelf tool below does), it'll look at all of the places it knows to look for Python code, the value of the variable PYTHONPATH is one of these places it'll look.


#### STEP 2) Add the following code to a new shelf tool:

```
import hdefereval

import megascans_asset
reload(megascans_asset) # optional (in the case you make a change to the code, this will make sure houdini doesn't use the pre-compiled version of the script it has)

hdefereval.executeDeferred(megascans_asset.main) # hdefereval is something fancy, it runs the function/method passed to it in the main thread (this is necessary because this shelf tool has UI which won't quit out properly unless this tool is run on the main thread)
```


