
import subprocess
import os.path as osp
import re
import xml.etree.ElementTree as ET
import sys
from . import fileutil
from . import utillib
import pdb


def get_cmd_output(cmd, cwd=None):
    try:
        output = subprocess.check_output(cmd, cwd=cwd)
        return output.decode('utf-8').strip()
    except subprocess.CalledProcessError:
        return None


class NotADotnetPackageError(Exception):

    def __init__(self, message):
        super(Exception, self).__init__(message)


class DotnetPackageInfo:

    SLN_EXTENTION = '.sln'
    PROJECT_EXTENTION = ['.csproj', '.vbproj', 'fsproj']

    SLN_FILES_TAG = 'sln_files'
    PROJ_FILES_TAG = 'proj_files'

    def __init__(self):
        pass

    def list_project_files(self, sln_file, pkg_build_dir):

        if not osp.isfile(osp.join(pkg_build_dir, sln_file)):
            raise FileNotFoundError(osp.join(pkg_build_dir, sln_file))

        _, _ext = osp.splitext(sln_file)

        if _ext != DotnetPackageInfo.SLN_EXTENTION:
            raise NotADotnetPackageError(osp.join(pkg_build_dir, sln_file))

        cmd = ['dotnet', 'sln', sln_file, 'list']

        proj_regex = re.compile(r'.+[.](csproj|vbproj|fsproj)$')
        for line in get_cmd_output(cmd, pkg_build_dir).split('\n'):
            if proj_regex.match(line) != None:
                yield line

    def get_target_framworks(self, proj_file):

        if not osp.isfile(proj_file):
            raise FileNotFoundError(proj_file)

        root = ET.parse(proj_file).getroot()

        if root.tag != 'Project':
            raise NameError('Not a C# Project file')

        for property_group in root.iter('PropertyGroup'):
            for elem in property_group:
                if elem.tag == 'TargetFramework':
                    return [elem.text.strip()]
                elif elem.tag == 'TargetFrameworks':
                    return [ _elm.strip() for _elm in elem.text.split(';')]

        return list()

    def get_project_config_plat(self, sln_file):

        file_lines = list()
        with open(sln_file) as fobj:
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
                return proj_conf_lines

            i = i + 1

    def solution_info(self, sln_file):

        file_lines = list()

        with open(sln_file) as fobj:
            file_lines = [_line.strip('\n') for _line in fobj]

        #proj_file_list = [_file for _file in self.list_project_files(osp.basename(sln_file), osp.dirname(sln_file))]

        proj_line_regex = re.compile(r'\s*Project\("{[^}]+}"\)\s*=\s*"[^"]+",\s*"(?P<project_file>.+[.](csproj|vbproj|fsproj))",\s*"{(?P<project_hash>[^}]+)}"')

        proj_info = dict()

        for _line in file_lines:
            match = proj_line_regex.match(_line)

            if match:
                proj_info[match.groupdict()['project_hash']] = {'project_file': match.groupdict()['project_file'].replace("\\", "/"),
                                                                'configuration': list()
                                                                }

        proj_config_plat = self.get_project_config_plat(sln_file)
        config_plat_regex = re.compile(r'{(?P<project_hash>[^}]+)}[.](Debug|Release)[|]Any\s*CPU[.]ActiveCfg\s*=\s*(?P<configuration>.+)[|].+')
        for config_plat in proj_config_plat:
            match = config_plat_regex.match(config_plat)

            if match:
                _hash = match.groupdict()['project_hash']
                if _hash in proj_info.keys():
                    proj_info[_hash]['configuration'].append(match.groupdict()['configuration'])

        new_proj_info = dict()

        for _value in proj_info.values():
            new_dict = dict()
            new_dict['configuration'] = _value['configuration']
            new_dict['framworks'] = self.get_target_framworks(osp.join(osp.dirname(sln_file), _value['project_file']))
            new_proj_info[_value['project_file']] = new_dict

        return new_proj_info


    def get_sln_files(self, pkg):
        return fileutil.get_file_list(pkg, [], [DotnetPackageInfo.SLN_EXTENTION])

    def get_project_files(self, pkg):
        return fileutil.get_file_list(pkg, [], DotnetPackageInfo.PROJECT_EXTENTION)

    def is_valid(self, pkg):
        '''Checks if it is a valid dotnet package'''

        if osp.isdir(pkg):
            sln_files = self.get_sln_files(pkg)

            if len(sln_files) == 0:
                proj_files = self.get_project_files(pkg)

                if len(proj_files) == 0:
                    return False
            return True
        else:
            name, _ext = osp.splitext(pkg)

            if osp.isfile(pkg) and (_ext in DotnetPackageInfo.PROJECT_EXTENTION or _ext == DotnetPackageInfo.SLN_EXTENTION):
                return True
            else:
                return False

    def get_pkg_info(self, pkg):
        '''
        :param pkg_dir: it can be a directory, path to a sln file or a project file
        :return: pkg_info

        {
          'sln_files': {
             '1.sln': [
                 '1.proj',
                 '2.proj',
             ],
             '2.sln': [
                 '1.proj',
                 '3.proj'
             ]
          },
          'proj_files' : {
             '1.proj' : {
                'frameworks' : ['fw1', 'fw2'],
                'configurations' : ['conf1', 'conf2'],
             },
             '2.proj' : {
                'frameworks' : ['fw1', 'fw2'],
                'configurations' : ['conf1', 'conf2'],
             }
          }
        }
        '''

        pkg_info = dict()

        if not self.is_valid(pkg):
            raise NotADotnetPackageError(pkg)

        if osp.isdir(pkg):
            sln_files = self.get_sln_files(pkg)

            if sln_files:
                pkg_info[DotnetPackageInfo.SLN_FILES_TAG] = dict()
                pkg_info[DotnetPackageInfo.PROJ_FILES_TAG] = dict()

                for _file in sln_files:
                    sln_info = self.solution_info(_file)
                    pkg_info[DotnetPackageInfo.SLN_FILES_TAG][_file] = list(sln_info.keys())
                    pkg_info[DotnetPackageInfo.PROJ_FILES_TAG].update(sln_info)

            else:
                project_files = self.get_project_files(pkg)

                if project_files:
                    proj_info = dict()

                    for _file in project_files:
                        proj_info[_file] = { 'frameworks': self.get_target_framworks(_file) }

                    pkg_info[DotnetPackageInfo.PROJ_FILES_TAG] = proj_info
                else:
                    raise NotADotnetPackageError(pkg)
        else:
            name, ext = osp.splitext(pkg)
            if ext == DotnetPackageInfo.SLN_EXTENTION:
                pkg_info[DotnetPackageInfo.SLN_FILES_TAG] = dict()
                pkg_info[DotnetPackageInfo.PROJ_FILES_TAG] = dict()

                sln_info = self.solution_info(pkg)
                pkg_info[DotnetPackageInfo.SLN_FILES_TAG][pkg] = list(sln_info.keys())
                pkg_info[DotnetPackageInfo.PROJ_FILES_TAG] = sln_info

            elif ext in DotnetPackageInfo.PROJECT_EXTENTION:
                pkg_info[DotnetPackageInfo.PROJ_FILES_TAG] = dict()
                proj_info = dict()
                proj_info[pkg] = {'frameworks': self.get_target_framworks(pkg)}
                pkg_info[DotnetPackageInfo.PROJ_FILES_TAG] = proj_info

        return pkg_info
