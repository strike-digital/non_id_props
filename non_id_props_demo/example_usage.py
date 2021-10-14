import bpy
from .non_id_props import NonIDProperty


def my_vertex_group_update(self, context):
    print(f"My vertex group is called '{self.my_vertex_group.name if self.my_vertex_group else self.my_vertex_group}'")


class MyPropertyGroup(bpy.types.PropertyGroup):

    # Make sure to assign with an '=' rather than a ':' like other Blender properties
    my_vertex_group = NonIDProperty(
        name="my_vertex_group",  # THIS MUST BE THE SAME AS THE NAME OF THE VARIABLE
        # (Someone please tell me if theres a better way :)
        subtype="vertex_groups",  # This is the path to the non id property, from its parent ID property
        # e.g. object.vertex_groups
        set=my_vertex_group_update,  # The get, set, and update functions work in the same way as default Blender
    )

    # Note that the subtype can only be of a subtype of the ID property this group is registered to
    # (In this case, bpy.types.Object)
    my_modifier = NonIDProperty(
        name="my_modifier",
        subtype="modifiers",
    )

    my_constraint = NonIDProperty(
        name="my_constraint",
        subtype="constraints",
    )


classes = [MyPropertyGroup]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.non_id_prop_demo = bpy.props.PointerProperty(type=MyPropertyGroup)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.non_id_prop_demo
