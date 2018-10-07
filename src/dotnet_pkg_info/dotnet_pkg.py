
import json
import os.path as osp
import xml.etree.ElementTree as ET
import re
from . import fileutil
from .errors_warnings import DotnetPackageError
from .errors_warnings import InvalidSolutionFile

import pdb


class DotnetPackage:

    SLN_FILES_TAG = 'sln_files'
    PROJ_FILES_TAG = 'proj_files'

    @classmethod
    def is_valid(cls, pkg_dir):

        # Check if it is a directory
        # Check if it is a file with .sln or .proj extentions
        # Check if it has permissions
        # Check if there are .sln or .proj files
        # TODO fill in
        return True

    def __init__(self, pkg_dir):
        self.pkg_dir = pkg_dir
        self.sln_files = set()  # SLN file object
        self.proj_files = set()  # Proj file object
        self.errors = set()
        self.warnings = set()

    def set_pkg_dir(self, pkg_dir):
        self.pkg_dir = pkg_dir

    def add_sln_file(self, sln_file_obj):
        self.sln_files.add(sln_file_obj)

    def add_proj_file(self, proj_file_obj):
        self.proj_files.add(proj_file_obj)

    def add_error(self, error):
        self.errors.add(error)

    def to_json(self):
        json_dict = dict()

        if self.sln_files:
            json_dict[DotnetPackage.SLN_FILES_TAG] = {
                _file.get_path(): _file.get_project_files() for _file in self.sln_files
            }
        
        json_dict[DotnetPackage.PROJ_FILES_TAG] = {
                _file.get_path(): _file.to_json() for _file in self.proj_files
        }

        return json_dict


class SolutionFile:
    SLN_EXTENTION = '.sln'

    @classmethod
    def is_valid(cls, sln_file, pkg_dir=None):
        #TODO fill in
        return True

    @classmethod
    def get_sln_files(cls, pkg_dir):
        return fileutil.get_file_list(pkg_dir, [], [SolutionFile.SLN_EXTENTION])

    def __init__(self, sln_file, pkg_dir=None):
        self.sln_file = sln_file
        self.pkg_dir = pkg_dir
        self.proj_files_hash = dict()

    def get_path(self):
        return self.sln_file

    def set_project_files(self):

        with open(osp.join(self.pkg_dir, self.sln_file)) as fobj:
            file_lines = [_line.strip('\n') for _line in fobj]

            proj_line_regex = re.compile(r'\s*Project\("{[^}]+}"\)\s*=\s*"[^"]+",\s*"(?P<project_file>.+[.](csproj|vbproj|fsproj))",\s*"{(?P<project_hash>[^}]+)}"')

            for _line in file_lines:
                match = proj_line_regex.match(_line)

                if match:
                    proj_hash = match.groupdict()['project_hash']
                    proj_file = match.groupdict()['project_file'].replace("\\", "/")
                    self.proj_files_hash[proj_file] = proj_hash

    def get_project_files(self):
        return list(self.proj_files_hash.keys())

    def _get_project_config_plat(self):

        file_lines = list()
        with open(osp.join(self.pkg_dir, self.sln_file)) as fobj:
            file_lines = [_line.strip('\n') for _line in fobj]

        pgp_re = re.compile(r'\s*GlobalSection\(ProjectConfigurationPlatforms\)\s*=\s*postSolution\s*')
        proj_conf_lines = list()

        i = 0
        while i < len(file_lines):
            match = pgp_re.match(file_lines[i])

            if match:
                i = i + 1
                while file_lines[i].strip() != 'EndGlobalSection':
                    proj_conf_lines.append(file_lines[i].strip())
                    i = i + 1
                break

            i = i + 1

        return proj_conf_lines

    def get_configuration(self, project_file):

        configuration = list()
        proj_hash = self.proj_files_hash[project_file]

        config_plat_regex = re.compile(r'{(?P<project_hash>[^}]+)}[.](Debug|Release)[|]Any\s*CPU[.]ActiveCfg\s*=\s*(?P<configuration>.+)[|].+')

        for config_plat in self._get_project_config_plat():
            match = config_plat_regex.match(config_plat)

            if match:
                if match.groupdict()['project_hash'] == proj_hash:
                    configuration.append(match.groupdict()['configuration'])

        return configuration

    def to_json(self):
        pass


class ProjectFile:
    PROJECT_EXTENTION = {'.csproj', '.vbproj', 'fsproj'}

    CORE_TARGET_FRAMEWORKS = {'netstandard1.0',
                              'netstandard1.1',
                              'netstandard1.2',
                              'netstandard1.3',
                              'netstandard1.4',
                              'netstandard1.5',
                              'netstandard1.6',
                              'netstandard2.0',
                              'netcoreapp1.0',
                              'netcoreapp1.1',
                              'netcoreapp2.0',
                              'netcoreapp2.1',
                              'uap',
                              'uap10.0'
                              }

    TARGET_FRAMEWORK_TAG = 'TargetFramework'
    TARGET_FRAMEWORKS_TAG = 'TargetFrameworks'


    @classmethod
    def is_valid(cls, proj_file, pkg_dir=None):
        #TODO fill in
        return True

    @classmethod
    def get_project_files(cls, pkg_dir):
        return fileutil.get_file_list(pkg_dir, [], ProjectFile.PROJECT_EXTENTION)

    def __init__(self, proj_file, pkg_dir=None):
        self.proj_file = proj_file
        self.pkg_dir = pkg_dir

        self.frameworks = set()
        self.configurations = set()
        self.default_framework = None
        self.default_configuration = None

    def get_path(self):
        return self.proj_file

    def set_target_frameworks(self):

        proj_file = self.proj_file

        if not osp.isabs(proj_file):
            proj_file = osp.join(self.pkg_dir, proj_file)

        root = ET.parse(proj_file).getroot()

        for property_group in root.iter('PropertyGroup'):
            for elem in property_group:
                if elem.tag == ProjectFile.TARGET_FRAMEWORK_TAG:
                    self.frameworks = {elem.text.strip()}
                elif elem.tag == ProjectFile.TARGET_FRAMEWORKS_TAG:
                    self.frameworks = {_elm.strip() for _elm in elem.text.split(';')}

    def set_build_configurations(self, conf_list):
        self.configurations = list(conf_list)

    def set_default_framework(self):

        if len(self.frameworks.intersection(ProjectFile.CORE_TARGET_FRAMEWORKS)):
            self.default_framework = None

        for tmf in ProjectFile.CORE_TARGET_FRAMEWORKS:
            if tmf in self.frameworks:
                self.default_framework = tmf
                break

    def set_default_configurations(self):

        if 'Debug' in self.configurations:
            self.default_configuration = 'Debug'
        else:
            self.default_configuration = self.configurations[0]

    def to_json(self):
        json_dict = {
                'frameworks': list(self.frameworks),
        }

        if self.configurations:
            json_dict['configurations'] = list(self.configurations),

        if self.default_framework:
            json_dict['default_framework'] = self.default_framework

        if self.default_configuration:
            json_dict['default_configuration'] = self.default_configuration

        return json_dict


def main_isdir(package):

    dpkg = DotnetPackage(package)
    try:
        DotnetPackage.is_valid(package)

        package = osp.abspath(package)
        dpkg.set_pkg_dir(package)

        sln_files = SolutionFile.get_sln_files(package)

        if sln_files:
            sln_file_objs = [SolutionFile(osp.relpath(_file, package), package) \
                             for _file in sln_files]

            for sln_obj in sln_file_objs:

                try:
                    if SolutionFile.is_valid(sln_obj):
                        sln_obj.set_project_files()
                        dpkg.add_sln_file(sln_obj)

                        for proj_file in sln_obj.get_project_files():
                            proj_file_obj = ProjectFile(proj_file,
                                                        osp.join(package,
                                                                 osp.dirname(sln_obj.get_path())))
                            proj_file_obj.set_target_frameworks()
                            proj_file_obj.set_build_configurations(sln_obj.get_configuration(proj_file))
                            proj_file_obj.set_default_framework()
                            proj_file_obj.set_default_configurations()
                            dpkg.add_proj_file(proj_file_obj)

                except InvalidSolutionFile as err:
                    dpkg.add_error(err)
        else: # No solution files

            for proj_file in ProjectFile.get_project_files(package):
                proj_file_obj = ProjectFile(osp.relpath(proj_file, package),
                                            package)
                proj_file_obj.set_target_frameworks()
                proj_file_obj.set_default_framework()
                dpkg.add_proj_file(proj_file_obj)

    except DotnetPackageError as err:
        dpkg.add_error(err)

    return dpkg


def main_slnfile(sln_file):

    sln_file = osp.abspath(sln_file)
    dpkg = DotnetPackage(sln_file)
    pkg_dir = osp.dirname(sln_file)
    dpkg.set_pkg_dir(pkg_dir)

    try:
        if SolutionFile.is_valid(sln_file):

            sln_obj = SolutionFile(osp.relpath(sln_file, pkg_dir), pkg_dir)
            sln_obj.set_project_files()
            dpkg.add_sln_file(sln_obj)

            for proj_file in sln_obj.get_project_files():
                proj_file_obj = ProjectFile(proj_file,
                                            osp.join(pkg_dir,
                                                     osp.dirname(sln_obj.get_path())))
                proj_file_obj.set_target_frameworks()
                proj_file_obj.set_build_configurations(sln_obj.get_configuration(proj_file))
                proj_file_obj.set_default_framework()
                proj_file_obj.set_default_configurations()
                dpkg.add_proj_file(proj_file_obj)

    except InvalidSolutionFile as err:
        dpkg.add_error(err)

    except DotnetPackageError as err:
        dpkg.add_error(err)

    return dpkg


def main_projfile(proj_file):

    proj_file = osp.abspath(proj_file)
    dpkg = DotnetPackage(proj_file)
    pkg_dir = osp.dirname(proj_file)
    dpkg.set_pkg_dir(pkg_dir)

    try:
        proj_file_obj = ProjectFile(osp.relpath(proj_file, pkg_dir), pkg_dir)
        proj_file_obj.set_target_frameworks()
        proj_file_obj.set_default_framework()
        dpkg.add_proj_file(proj_file_obj)

    except DotnetPackageError as err:
        dpkg.add_error(err)

    return dpkg


def main(package):

    if osp.isdir(package):
        return main_isdir(package)
    else:
        path, ext = osp.splitext(package)

        if ext == SolutionFile.SLN_EXTENTION:
            return main_slnfile(package)
        elif ext in ProjectFile.PROJECT_EXTENTION:
            return main_projfile(package)
        else:
            raise InvalidSolutionFile()
