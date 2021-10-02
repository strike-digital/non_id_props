import bpy
from bpy import msgbus
from bpy.app.handlers import persistent
from bpy.props import StringProperty, CollectionProperty
from typing import Callable, Any

"""This works by using a combination of the builtin python getters and setter, and the blender msgbus module
* The setter is used to store the name of the given item as a Blender string
* The getter is then used to return the item with the stored name
* The msgbus module is then used to get updates when the name of the item is changed,
    and update the property accordingly

But every time a new file is loaded, all subscribers to the msgbus are lost,
so when a property is set it stores it's data in scene.non_id_props.
This is then read back by a handler when the file is loaded, and the msgbus subscribers are added agian
"""

# translates between ID type names and subclasses of bpy.data
types = {
    'Brush': 'brushes',
    'Scene': 'scenes',
    'GreasePencil': 'grease_pencils',
    'World': 'worlds',
    'NodeGroup': 'node_groups',
    'Object': 'objects',
    'Mask': 'masks',
    'Workspace': 'workspaces',
    'Metaball': 'metaballs',
    'Action': 'actions',
    'Armature': 'armatures',
    'Collection': 'collections',
    'Speaker': 'speakers',
    'WindowManager': 'window_managers',
    'Font': 'fonts',
    'Lightprobe': 'lightprobes',
    'ShapeKey': 'shape_keys',
    'Light': 'lights',
    'Text': 'texts',
    'PaintCurve': 'paint_curves',
    'Linestyle': 'linestyles',
    'Curve': 'curves',
    'Mesh': 'meshes',
    'Lattice': 'lattices',
    'Library': 'libraries',
    'CacheFile': 'cache_files',
    'Screen': 'screens',
    'Image': 'images',
    'Particle': 'particles',
    'Volume': 'volumes',
    'Sound': 'sounds',
    'Camera': 'cameras',
    'Palette': 'palettes',
    'Material': 'materials',
    'Texture': 'textures',
    'Movieclip': 'movieclips',
}


# Use this function to return the prop rather than the instance, idk if this is the best way to do it
def NonIDProperty(name: str, subtype: str,
                  get: Callable[[bpy.types.PropertyGroup, bpy.types.Context], Any] = None,
                  set: Callable[[bpy.types.PropertyGroup, bpy.types.Context, Any], Any] = None,
                  update: Callable[[bpy.types.PropertyGroup, bpy.types.Context], Any] = None) -> property:
    """Returns a property that can hold a reference to a blender property that is not a subclass of bpy.types.ID,
    even if that properties name is changed in the UI.

    Limitations:
        * This can only keep a reference to an item that is a subclass of the ID property type that it is registered to,
            e.g. a reference to a vertex group can only be created in a subclass of bpy.types.Object
        * The name argument must be the same as the name of the variable the property is being assigned to.

    Example usage:
        bpy.types.Object.vgroup = NonIDProperty(name="vgroup", subtype="vertex_groups")

    Args:
        name (str): THIS MUST BE THE SAME AS THE NAME OF THE VARIABLE THIS IS ASSIGNED TO.
        subtype (str): This is the path from the ID data block that this is currently registered to,
            to the non ID property you want to assign it to.
        get (function): Function that is called when the property is returned
        set (function): Function that is called when the property is set
        update (function): Function that is called when the property is updated

    Returns:
        property: a property that will still reference the item it is assigned to,
            even when the name of the item is changed
    """
    return _NonIDProperty(name, subtype, get, set, update).prop


class _NonIDProperty():

    def __init__(self, name, subtype, parent_get=None, parent_set=None, parent_update=None):
        self.subtype = subtype
        self.name = name
        self.prop_name = "_" + name
        self.parent_get = parent_get
        self.parent_set = parent_set
        self.parent_update = parent_update
        self.prop = property(self._get_prop, self._set_prop)
        # uses built in python getters and setters:
        # https://www.python-course.eu/python3_properties.php
        # It doesn't use decorator notation because then it doesn't pass parent_cls for some reason

    def _get_prop(self, parent_cls):
        """Return the item, from the name that is stored by the set function"""

        if self.parent_get:
            return self.parent_get(parent_cls, bpy.context)

        # gets the collection property
        col_prop = getattr(parent_cls.id_data, self.subtype)
        try:
            # get the name of the item of the collection property
            prop_name = parent_cls[self.prop_name]
        except KeyError:  # Not set yet
            return None
        try:
            # get the collection property item
            return_prop = col_prop[prop_name]
        except KeyError:  # Item has been removed
            raise AttributeError(f"'{str(col_prop)}'' has no item '{prop_name}', has probably been removed")
        return return_prop

    def _set_prop(self, parent_cls, value):
        """Set the property from the given item's name,
        add the msgbus subscriber, update the scene msgbus items"""

        # Check if the module has been registered
        try:
            _ = bpy.data.scenes[0].non_id_props
        except AttributeError:
            raise RuntimeError("The non_id_props module needs to be registered before it can be used")

        if self.parent_get and not self.parent_set:
            raise AttributeError(f"Property '{self.name}' is read-only")

        if value is None:
            self._reset_prop(parent_cls)  # Remove bl property and msgbus item
            return

        # Set the name property
        parent_cls[self.prop_name] = value.name

        # get the collection property
        parent_col = getattr(parent_cls.id_data, self.subtype)
        item_name = parent_cls[self.prop_name]
        # get the item from the collection property
        parent_item = parent_col[item_name]

        self._refresh_msgbus(parent_cls, parent_item)
        self._add_msgbus_item(parent_cls, parent_item)

        if self.parent_set:
            self.parent_set(parent_cls, bpy.context, parent_item)

        if self.parent_update:
            self.parent_update(parent_cls, bpy.context)

    def _reset_prop(self, parent_cls):
        try:
            del parent_cls[self.prop_name]
        except KeyError:
            pass
        self._remove_msgbus_item()

    def _refresh_msgbus(self, parent_cls, parent_item):
        """Refresh the message bus to the newly set items name.
        It will then call _on_change when the name is changed"""
        msgbus.clear_by_owner(self)
        subscribe_to = parent_item.path_resolve("name", False)

        global _on_change  # on_change must be a function rather than a method or msgbus doesn't like it
        msgbus.subscribe_rna(
            key=subscribe_to,
            owner=self,
            args=(self, parent_cls, parent_item),
            notify=_on_change,
        )

    def _add_msgbus_item(self, parent_cls, parent_item):
        """Adds an item that can be used to re-add the msgbuses correctly,
        when the file is loaded again"""

        # Adds it to all scenes because I couldn't figure out how to register the msgbus items to the window manager,
        # without it resetting every time the file was opened.
        for scene in bpy.data.scenes:
            for item in scene.non_id_props:
                if item.path == parent_cls.path_from_id() and item.name == self.name:
                    break
            else:
                item = scene.non_id_props.add()

            item.type = types[parent_cls.id_data.bl_rna.identifier]
            item.path = parent_cls.path_from_id()
            item.name = self.name
            item.non_id_prop_name = parent_item.name

    def _remove_msgbus_item(self):
        for scene in bpy.data.scenes:
            for i, item in enumerate(scene.non_id_props):
                if item.name == self.name:
                    scene.non_id_props.remove(i)


def _on_change(*args):
    """This is called when the target items' name changes.
    It just sets the property to the new item"""
    self, parent_cls, parent_item = args
    msgbus_items = bpy.data.scenes[0].non_id_props
    for item in msgbus_items:
        name = item.non_id_prop_name
        if name == parent_cls[self.prop_name] or parent_item.name == parent_cls[self.prop_name]:
            data_blocks = getattr(bpy.data, item.type)
            for data_block in data_blocks:
                try:
                    parent_cls = data_block.path_resolve(item.path)
                except ValueError:
                    continue
                setattr(parent_cls, item.name, parent_item)


class MsgbusItem(bpy.types.PropertyGroup):
    """Used to keep track of all msgbus items that are are added,
    so that they can be readded when the file is loaded again"""

    type: StringProperty(description="The subclass of bpy.data that the ID property is")

    path: StringProperty(description="The path from the ID property")

    name: StringProperty(description="The name of the property")

    non_id_prop_name: StringProperty(description="The name of the property")


@persistent
def non_id_prop_on_load(dummy):
    """Handler called when new file is loaded,
    checks for msgbus items that need to be readded"""

    scene = bpy.data.scenes[0]
    msgbus_items = scene.non_id_props
    for item in msgbus_items:
        data_blocks = getattr(bpy.data, item.type)
        for data_block in data_blocks:
            try:
                parent_cls = data_block.path_resolve(item.path)
            except ValueError:
                continue
            val = getattr(parent_cls, item.name)
            setattr(parent_cls, item.name, val)


classes = (
    MsgbusItem,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.app.handlers.load_post.append(non_id_prop_on_load)
    # I tried registering this to the window manager (so it would be file wide),
    # but for some reason it didn't save with the file,
    # and was reset when loading a new one
    bpy.types.Scene.non_id_props = CollectionProperty(type=MsgbusItem)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.app.handlers.load_post.remove(non_id_prop_on_load)
    del bpy.types.Scene.non_id_props
