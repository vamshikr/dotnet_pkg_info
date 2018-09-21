
from enum import Enum, unique
import json
import os.path as osp
import xml.etree.ElementTree as ET
import re
from . import fileutil


class DotnetPackage:

    def __init__(self, pkg_dir):
        self.sln_files = set()
        self.proj_files = set()
        self.errors = set()
        self.warnings = set()

    def to_json(self):
        pass


class SolutionFile:
    SLN_EXTENTION = '.sln'

    @classmethod
    def is_valid(cls, proj_file, pkg_dir=None):
        #TODO fill in
        return True

    @classmethod
    def get_sln_files(cls, pkg_dir):
        return fileutil.get_file_list(pkg_dir, [], [SolutionFile.SLN_EXTENTION])

    def __init__(self, sln_file, pkg_dir=None):
        self.sln_file = self.sln_file
        self.pkg_dir = pkg_dir
        self.proj_files_hash = dict()

    def _set_project_files(self):

        with open(self.file_path) as fobj:
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
        with open(self.sln_file) as fobj:
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

        proj_hash = self.proj_files_hash[project_file]

        config_plat_regex = re.compile(r'{(?P<project_hash>[^}]+)}[.](Debug|Release)[|]Any\s*CPU[.]ActiveCfg\s*=\s*(?P<configuration>.+)[|].+')

        for config_plat in self._get_project_config_plat():
            match = config_plat_regex.match(config_plat)

            if match:
                if match.groupdict()['project_hash'] == proj_hash:
                    return match.groupdict()['configuration']

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
    TARGET_FRAMEWORKS_TAG = 'TargetsFramework'


    @classmethod
    def is_valid(cls, proj_file, pkg_dir=None):
        #TODO fill in
        return True

        root = ET.parse(proj_file).getroot()

        if root.tag != 'Project':
            raise NameError('Not a C# Project file')

        for property_group in root.iter('PropertyGroup'):
            for elem in property_group:
                if elem.tag == ProjectFile.TARGET_FRAMEWORK_TAG:
                    self.frameworks = {elem.text.strip()}
                elif elem.tag == ProjectFile.TARGET_FRAMEWORKS_TAG:
                    self.frameworks = {_elm.strip() for _elm in elem.text.split(';')}

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
        # self.framework = None
        # self.configuration = None

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
            raise Exception()

        for tmf in ProjectFile.CORE_TARGET_FRAMEWORKS:
            if tmf in self.frameworks:
                self.default_framework = tmf
                break

    def set_default_configurations(self, conf_list):

        if 'Debug' in self.configuration:
            self.default_configuration = 'Debug'
        else:
            self.default_configuration = self.configurations

    def to_json(self):
        pass
