
# I know it's crazy, but yes, this is defining a name (which is assigned to a function). Name is synonymous with variable, right? Or is name what we call a variable used for libaries? I don't know what I'm saying.

# ensuring that the reload function we use is compatible with Python
try:
    foolproof_reload = reload # Python 2.7 has this
except:
    try:
        from importlib import reload as foolproof_reload # Python 3.4+ has this
    except:
        from imp import reload as foolproof_reload # Python 3.0 - 3.3 has this


# EDIT: Python 3 is fine with modules (python files) having variables (or "names" - I really don't know what the difference is) with the same names as iconic Python names like 'reload', 'math' (I presume, any names in use by default Python modules) --- but Python 2 is not fine with that, e.g. "from reload_helper import reload" or "import reload_helper; reload_helper.reload" would throw an error.
# ^ I say Python 3 and Python 2, but I really mean 3.7.4 and 2.7.15 respectively (Houdini's version's of Python at the time I tested this), also, Houdini might be doing weird stuff behind the scenes, so the jury is out.