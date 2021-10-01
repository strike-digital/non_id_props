# Non ID Props

This is a library that that allows you to store direct references to properties in Blender that are not subclasses of ```bpy.types.ID```

# But why???

In Blender you can use ```PointerProperties``` to keep references to datablocks in the current blend file, even when the name is changed. However, if you want to keep a reference to a property that is not a subclass of ```bpy.types.ID```, such as a vertex group, a PointerProperty won't work. The only option is to instead keep a reference to the name of the property, which makes code harder to read and write, and more importantly, means that if the name is changed by the user, the reference will no longer work.

This library changes that by providing a property that can not only be set to non subclasses of ```bpy.types.ID```, but can also keep them, even when the name is changed in the UI

# How do I use it?

Simply place the ```non_id_props.py``` file in your addon directory, *and make sure to register it*. Then import ```NonIDProperty``` and from there you can use it in much the same way as the builtin Blender properties, with some differences:
* Properties should be assigned with '=' rather than ':'
* The 'name' argument should ALWAYS be the same as the name of the variable that the NonIDProperty is being assigned to. (I'm sure there's a better way to do this, please tell me :)
* The subtype should be the path from the ID property to the subtype as a string, e.g. ```vertex_groups``` from ```object.vertex_groups```

Example usage:

```py
my_vgroup = NonIDProperty(
  name="my_prop",
  subtype="vertex_groups",
  update=my_vgroup_update_func,
  )
```

# Download
Get the latest release along with the demo addon here:
https://github.com/strike-digital/non_id_props/releases/latest