import sys
import json
from .dotnet_pkg import DotnetPackage
import os.path as osp

import pdb


def get_build_commands_old(build_settings):

    with open('build.sh', 'w') as fp:
        print('#! /usr/bin/env bash\n', file=fp)
        print('set -x\n', file=fp)
        print('cd {0}'.format(pkg_dir), file=fp)

        if 'sln_files' not in build_settings or len(build_settings['sln_files'].keys()) == 0:
            proj_files = list(build_settings['proj_files'].keys())

            for proj_file in proj_files:
                proj_info = build_settings['proj_files'][proj_file]

                if 'nobuild' not in proj_info:
                    cmd = 'dotnet build {0}  --framework {1} --configuration {2}'.format(proj_file,
                                                                                         proj_info['framework'],
                                                                                         proj_info.get('configuration',
                                                                                                       'Debug'))
                    ampamp = '&&' if (proj_files.index(proj_file) < len(proj_files) - 1) else ''
                    print("(\n\t{0}\n){1}\n\n".format(cmd, ampamp), file=fp)

        elif len(build_settings['sln_files'].keys()) == 1:
            sln_file = list(build_settings['sln_files'].keys())[0]
            proj_files = build_settings['sln_files'][sln_file]

            for proj_file in proj_files:
                proj_info = build_settings['proj_files'][proj_file]
                if 'nobuild' not in proj_info:
                    cmd = 'dotnet build {0}  --framework {1} --configuration {2}'.format(proj_file,
                                                                                         proj_info['framework'],
                                                                                         proj_info.get('configuration',
                                                                                                       'Debug'))
                    ampamp = '&&' if (proj_files.index(proj_file) < len(proj_files) - 1) else ''
                    print("(\n\t{0}\n){1}\n\n".format(cmd, ampamp), file=fp)


def get_build_command(build_file, target_framework=None, build_config=None):
    cmd = ['dotnet', 'build', '"{0}"'.format(build_file)]

    if target_framework:
        cmd.append('--framework')
        cmd.append(target_framework)

    if build_config:
        cmd.append('--configuration')
        cmd.append(build_config)

    return cmd


def get_build_commands(build_settings):

    build_commands = list()

    if DotnetPackage.SLN_FILES_TAG and \
       build_settings[DotnetPackage.SLN_FILES_TAG]:

        # There is only one sln_file always
        sln_file = list(build_settings[DotnetPackage.SLN_FILES_TAG].keys())[0]

        # if no proj files listed
        if len(build_settings[DotnetPackage.SLN_FILES_TAG][sln_file]) == 0:
            build_commands.append(get_build_command(sln_file))
        else:
            # When there are one or more proj files 
            projects = build_settings[DotnetPackage.PROJ_FILES_TAG]

            for proj in build_settings[DotnetPackage.SLN_FILES_TAG][sln_file]:

                if projects[proj].get('nobuild', 'false') == 'false':
                    build_commands.append(get_build_command(osp.join(osp.dirname(sln_file), proj),
                                                            projects[proj].get('framework'),
                                                            projects[proj].get('configuration')))

            else:
                # When there are no sln files, but projects
                projects = build_settings[DotnetPackage.PROJ_FILES_TAG]

                for proj in projects.keys():
                    if projects[proj].get('nobuild', 'false') == 'false':
                        build_commands.append(get_build_command(osp.join(osp.dirname(sln_file), proj),
                                                                projects[proj].get('framework'),
                                                                projects[proj].get('configuration')))

    return {'build_commands': build_commands} 


def print_text(build_commands):

    for cmd in build_commands['build_commands']:
        print(' '.join(cmd))


def main(json_str, to_json):
    build_settings = json.loads(json_str)
    build_commands = get_build_commands(build_settings)

    if to_json:
        json.dump(build_commands, sys.stdout)
    else:
        print_text(build_commands)

