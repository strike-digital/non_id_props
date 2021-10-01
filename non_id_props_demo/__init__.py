"""To use this demo, install this addon (either from a zip, or by placing it in the addons folder),
    and then in the python console, and find 'C.object.non_id_prop_demo.my_vertex_group'.

You can then try setting it to a vertex group on that object with:
'my_vertex_group = C.object.vertex_groups[0]'.

Notice how it is being set to the actual property rather than it's name, and also that,
if you then get it's value, it also returns the property.

Then try changing the name of the vertex group in the UI. When only storing the name (the normal method),
this would mean that the property no longer works,
but using this system, the property will still reference the same vertex group.
"""

import bpy  # noqa F401
from . import non_id_props, example_usage

bl_info = {
    "name": "Non id props demo",
    "author": "Andrew Stevenson",
    "description": "A demo on how to use the non_id_props library",
    "blender": (2, 93, 0),
    "version": (1, 0, 0),
    "location": "bpy.context.object.non_id_prop_demo.my_vertex_group",
    "wiki_url": "",
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "Development"
}

# Make sure to register the non_id_props module
modules = [
    non_id_props,
    example_usage
]


if "bpy" in locals():
    import imp
    for m in modules:
        imp.reload(m)


def register():
    for module in modules:
        if hasattr(module, "register"):
            module.register()


def unregister():
    for module in modules:
        if hasattr(module, "unregister"):
            module.unregister()
