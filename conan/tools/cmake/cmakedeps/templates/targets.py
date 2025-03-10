import textwrap

from conan.tools.cmake.cmakedeps.templates import CMakeDepsFileTemplate

"""

FooTargets.cmake

"""


class TargetsTemplate(CMakeDepsFileTemplate):

    @property
    def filename(self):
        name = "" if not self.find_module_mode else "module-"
        name += self.file_name + "Targets.cmake"
        return name

    @property
    def context(self):
        data_pattern = "${_DIR}/" if not self.find_module_mode else "${_DIR}/module-"
        data_pattern += "{}-*-data.cmake".format(self.file_name)

        target_pattern = "" if not self.find_module_mode else "module-"
        target_pattern += "{}-Target-*.cmake".format(self.file_name)

        cmake_target_aliases = self.conanfile.cpp_info.\
            get_property("cmake_target_aliases") or dict()

        target = self.root_target_name
        cmake_target_aliases = {alias: target for alias in cmake_target_aliases}

        cmake_component_target_aliases = dict()
        for comp_name in self.conanfile.cpp_info.components:
            if comp_name is not None:
                aliases = \
                    self.conanfile.cpp_info.components[comp_name].\
                    get_property("cmake_target_aliases") or dict()

                target = self.get_component_alias(self.conanfile, comp_name)
                cmake_component_target_aliases[comp_name] = {alias: target for alias in aliases}

        ret = {"pkg_name": self.pkg_name,
               "root_target_name": self.root_target_name,
               "file_name": self.file_name,
               "data_pattern": data_pattern,
               "target_pattern": target_pattern,
               "cmake_target_aliases": cmake_target_aliases,
               "cmake_component_target_aliases": cmake_component_target_aliases}

        return ret

    @property
    def template(self):
        return textwrap.dedent("""\
        # Load the debug and release variables
        get_filename_component(_DIR "${CMAKE_CURRENT_LIST_FILE}" PATH)
        file(GLOB DATA_FILES "{{data_pattern}}")

        foreach(f ${DATA_FILES})
            include(${f})
        endforeach()

        # Create the targets for all the components
        foreach(_COMPONENT {{ '${' + pkg_name + '_COMPONENT_NAMES' + '}' }} )
            if(NOT TARGET ${_COMPONENT})
                add_library(${_COMPONENT} INTERFACE IMPORTED)
                conan_message(STATUS "Conan: Component target declared '${_COMPONENT}'")
            else()
                message(WARNING "Component target name '${_COMPONENT}' already exists.")
            endif()
        endforeach()

        if(NOT TARGET {{ root_target_name }})
            add_library({{ root_target_name }} INTERFACE IMPORTED)
            conan_message(STATUS "Conan: Target declared '{{ root_target_name }}'")
        endif()

        {%- for alias, target in cmake_target_aliases.items() %}

        if(NOT TARGET {{alias}})
            add_library({{alias}} INTERFACE IMPORTED)
            set_property(TARGET {{ alias }} PROPERTY INTERFACE_LINK_LIBRARIES {{target}})
        else()
            message(WARNING "Target name '{{alias}}' already exists.")
        endif()

        {%- endfor %}

        {%- for comp_name, component_aliases in cmake_component_target_aliases.items() %}

            {%- for alias, target in component_aliases.items() %}

        if(NOT TARGET {{alias}})
            add_library({{alias}} INTERFACE IMPORTED)
            set_property(TARGET {{ alias }} PROPERTY INTERFACE_LINK_LIBRARIES {{target}})
        else()
            message(WARNING "Target name '{{alias}}' already exists.")
        endif()

            {%- endfor %}

        {%- endfor %}

        # Load the debug and release library finders
        get_filename_component(_DIR "${CMAKE_CURRENT_LIST_FILE}" PATH)
        file(GLOB CONFIG_FILES "${_DIR}/{{ target_pattern }}")

        foreach(f ${CONFIG_FILES})
            include(${f})
        endforeach()
        """)
