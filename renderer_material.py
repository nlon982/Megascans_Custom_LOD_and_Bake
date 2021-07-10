import abc

ABC = abc.ABCMeta('ABC', (object,), {'__slots__': ()})  # from stack overflow https://stackoverflow.com/questions/35673474/using-abc-abcmeta-in-a-way-it-is-compatible-both-with-python-2-7-and-python-3-5

class RendererMaterial(ABC):
    @staticmethod
    @abc.abstractmethod
    def get_renderer_name():
        pass

    @staticmethod
    @abc.abstractmethod
    def get_template_map_name_and_node_setup_dict():
        """
        Return (a copy of) map_name_and_node_setup_dict. Why a copy? Fool proofing - so that way we don't rely on the callee to do this, i.e. the callee might forget to make a copy and change it (it shouldn't be changed)
        """
        pass

    @abc.abstractmethod
    def configure_megascans_asset_subnet(self, megascans_asset_object):
        """
        Is there any <render name goes here> specific parameters, or other actions, in the Megascans Asset's Subnet that
        need to be configured? (i.e. anything Megascans forgets)

        Feel free to use self and/or megascans_asset_object to do so.
        """
        pass

    @abc.abstractmethod
    def get_material_builder_node(self):
        """
        Return a node that nodes will be added to (as per redshift_map_name_and_node_setup_dict)
        """
        pass



class RedshiftMaterial(RendererMaterial):
    """
    Represents a particular Redshift Material in Houdini
    """
    # static attribute, rather than instance attribute, because this need not be instantiated for each instance
    redshift_map_name_and_node_setup_dict = dict()
    redshift_map_name_and_node_setup_dict["Displacement"] = "cTextureSampler-CB_Displacement_1!tex0:{export_path} i0 cDisplacement-CB_Displacement_2!map_encoding:2!space_type:1 i0"  # Map Encoding 0 is Vector, 2 is Height Field. Space Type 1 is object, 2 is Tangent.
    redshift_map_name_and_node_setup_dict["Vector Displacement"] = "cTextureSampler-CB_Vector_Displacement_1!tex0:{export_path} i0 cDisplacement-CB_Vector_Displacement_2!map_encoding:0!space_type:1 i0"
    redshift_map_name_and_node_setup_dict["Tangent-Space Vector Displacement"] = "cTextureSampler-CB_Tangent-Space_Vector_Displacement_1!tex0:{export_path} i0 cDisplacement-CB_Tangent-Space_Vector_Displacement_2!map_encoding:0!space_type:2 i0"
    redshift_map_name_and_node_setup_dict["Tangent-Space Normal"] = "@cNormalMap-CB_Tangent-Space_Normal!tex0:{export_path}"
    redshift_map_name_and_node_setup_dict["Occlusion"] = "@cTextureSampler-CB_Occlusion!tex0:{export_path}"
    redshift_map_name_and_node_setup_dict["Cavity"] = "@cTextureSampler-CB_Cavity!tex0:{export_path}"
    redshift_map_name_and_node_setup_dict["Thickness"] = "@cTextureSampler-CB_Thickness!tex0:{export_path}"
    redshift_map_name_and_node_setup_dict["Curvature"] = "@cTextureSampler-CB_Curvature!tex0:{export_path}"
    redshift_map_name_and_node_setup_dict["Shading Position"] = "@cTextureSampler-CB_Shading_Position!tex0:{export_path}"
    redshift_map_name_and_node_setup_dict["Shading Normal"] = "@cTextureSampler-CB_Shading_Normal!tex0:{export_path}"

    # it makes sense that the following are static methods because these need not need an instance (so it would be weird if they were instance methods)
    # note in Python (I forget re: Java), a static method can be called via a method call on the instance or of the class itself, e.g. a_redshiftmaterial_object.get_renderer_name() or RedshiftMaterial.get_render_name()
    @staticmethod
    def get_renderer_name():
        return "Redshift"

    @staticmethod
    def get_template_map_name_and_node_setup_dict():
        return RedshiftMaterial.redshift_map_name_and_node_setup_dict.copy() # is this elegant?

    def configure_megascans_asset_subnet(self, megascans_asset_object):
        # Enable Tessellation, Displacement, and set Displacement Scale
        megascans_asset_object.asset_geometry_node.parm("RS_objprop_rstess_enable").set(1)
        megascans_asset_object.asset_geometry_node.parm("RS_objprop_displace_enable").set(1)

        displacement_scale = megascans_asset_object.transform_node.parm("scale").eval()  # retrieved from transform_node after file import
        megascans_asset_object.asset_geometry_node.parm("RS_objprop_displace_scale").set(displacement_scale)
        print("enabled Tessellation, Displacement, and set Displacement Scale")

    def __init__(self, asset_material_node_child):
        self.rs_material_builder_node = asset_material_node_child

        redshift_material_node = None
        for child in self.rs_material_builder_node.children():
            if child.type().name() == "redshift_material":
                redshift_material_node = child
                break

        if redshift_material_node == None:
            raise Exception("Cannot find node of type 'redshift_material' in RS Material Builder")

    def get_material_builder_node(self):
        return self.rs_material_builder_node