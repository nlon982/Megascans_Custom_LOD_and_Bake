import abc

ABC = abc.ABCMeta('ABC', (object,), {'__slots__': ()})  # from stack overflow https://stackoverflow.com/questions/35673474/using-abc-abcmeta-in-a-way-it-is-compatible-both-with-python-2-7-and-python-3-5

class RendererMaterial(ABC):
    @abc.abstractmethod
    def get_renderer_name(self):
        pass

    @abc.abstractmethod
    def configure_megascans_subnet(self, megascan_asset_object):
        """
        Is there any <render name goes here> specific parameters, or other actions, in the Megascans Asset's Subnet that
        need to be configured? (i.e. anything Megascans forgets)
        """
        pass

    @abc.abstractmethod
    def get_material_builder_node(self):
        """
        Return a node that nodes will be added to (as per redshift_map_name_and_node_setup_dict)
        """
        pass

    @abc.abstractmethod
    def get_template_map_name_and_node_setup_dict(self):
        """
        Return a copy (fool proofing - so that way we don't rely on the callee) of the map_name_and_node_setup_dict
        """
        pass

class RedshiftMaterial:
    """
    Represents a Redshift Material
    """
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

    def __init__(self, asset_material_node_child):
        self.rs_material_builder_node = asset_material_node_child

        redshift_material_node = None
        for child in self.rs_material_builder_node.children():
            if child.type().name() == "redshift_material":
                redshift_material_node = child
                break

        if redshift_material_node == None:
            raise Exception("Cannot find node of type 'redshift_material' in RS Material Builder")

    def get_renderer_name(self):
        return "Redshift"

    def configure_megascans_subnet(self, megascan_asset_object):
        # Enable Tessellation, Displacement, and set Displacement Scale
        megascan_asset_object.asset_geometry_node.parm("RS_objprop_rstess_enable").set(1)
        megascan_asset_object.asset_geometry_node.parm("RS_objprop_displace_enable").set(1)

        displacement_scale = megascan_asset_object.transform_node.parm("scale").eval()  # retrieved from transform_node after file import
        megascan_asset_object.asset_geometry_node.parm("RS_objprop_displace_scale").set(displacement_scale)

    def get_material_builder_node(self):
        return self.rs_material_builder_node

    def get_template_map_name_and_node_setup_dict(self):
        return RedshiftMaterial.redshift_map_name_and_node_setup_dict.copy() # is this elegant?