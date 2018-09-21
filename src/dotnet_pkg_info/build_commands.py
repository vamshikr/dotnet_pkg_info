import json
import copy
import pprint
from .dotnet_pkg_info import DotnetPackageInfo
from .errors_warnings import DotnetPackageError


def verify_and_merge(build_settings, pkg_dir):
    dpi = DotnetPackageInfo()
    pkg_info = dpi.get_pkg_info(pkg_dir)

    new_pkg_info = copy.deepcopy(pkg_info)

    build_settings = json.loads(build_settings)

    # Verify if sln file in build_settings exist in pkg_info
    if 'sln_files' in build_settings and len(build_settings['sln_files'].keys()) > 0:
        sln_file = list(build_settings['sln_files'].keys())[0]

        if sln_file not in pkg_info['sln_files'].keys():
            new_pkg_info['errors'].append(DotnetPackageError(file_path=sln_file).to_json())
        else:
            # Verify if projects in sln array exist
            bs_proj_files = set(build_settings['sln_files'][sln_file])

            if len(bs_proj_files.difference(set(pkg_info['proj_files'].keys()))) > 0:
                new_pkg_info['errors'].extend(DotnetPackageError(file_path=proj_file).to_json()\
                                              for proj_file in bs_proj_files.difference(set(pkg_info['proj_files'].keys())))

    for bs_proj_file in build_settings['proj_files'].keys():

        if bs_proj_file in pkg_info['proj_files'].keys():
            bs_proj_info = build_settings['proj_files'][bs_proj_file]

            if 'framework' in bs_proj_info and \
                    bs_proj_info['framework'] in pkg_info['proj_files'][bs_proj_file]['frameworks']:
                new_pkg_info['proj_files'][bs_proj_file]['framework'] = bs_proj_info['framework']

            if 'configuration' in bs_proj_info and \
                    bs_proj_info['configuration'] in pkg_info['proj_files'][bs_proj_file]['configurations']:
                new_pkg_info['proj_files'][bs_proj_file]['configuration'] = bs_proj_info['configuration']


    return new_pkg_info


def get_build_settings(json_file, pkg_dir):

    with open(json_file) as fobj:
        pkg_info = json.load(fobj)

    build_settings = dict()

    if len(pkg_info['sln_files'].keys()) == 0:

        build_settings = copy.deepcopy(pkg_info)

        if 'proj_files' in pkg_info:
            for proj_file in pkg_info['proj_files'].keys():

                proj_info = pkg_info['proj_files'][proj_file]

                if 'default_framework' not in proj_info:
                    build_settings['proj_files'][proj_file]['nobuild'] = "true"

                # if 'frameworks' in build_settings['proj_files'][proj_file]:
                #     del(build_settings['proj_files'][proj_file]['frameworks'])
                #
                # if 'default_framework' in build_settings['proj_files'][proj_file]:
                #     del(build_settings['proj_files'][proj_file]['default_framework'])
                #
                # if 'configurations' in build_settings['proj_files'][proj_file]:
                #     del(build_settings['proj_files'][proj_file]['configurations'])
                #
                # if 'default_configuration' in build_settings['proj_files'][proj_file]:
                #     del(build_settings['proj_files'][proj_file]['default_configuration'])

    elif len(pkg_info['sln_files'].keys()) == 1:
        build_settings = copy.deepcopy(pkg_info)
        sln_file = list(pkg_info['sln_files'].keys())[0]

        build_settings['sln_files'][sln_file] = list(build_settings['sln_files'][sln_file])
        if 'proj_files' in pkg_info:
            for proj_file in pkg_info['sln_files'][sln_file]:

                proj_info = pkg_info['proj_files'][proj_file]

                if 'default_framework' not in proj_info:
                    build_settings['proj_files'][proj_file]['nobuild'] = "true"
                    build_settings['sln_files'][sln_file].remove(proj_file)
                else:
                    build_settings['proj_files'][proj_file]['framework'] = build_settings['proj_files'][proj_file]['default_framework']

                build_settings['proj_files'][proj_file]['configuration'] = build_settings['proj_files'][proj_file][
                    'default_configuration']

                if 'frameworks' in build_settings['proj_files'][proj_file]:
                    del(build_settings['proj_files'][proj_file]['frameworks'])

                if 'default_framework' in build_settings['proj_files'][proj_file]:
                    del(build_settings['proj_files'][proj_file]['default_framework'])

                if 'configurations' in build_settings['proj_files'][proj_file]:
                    del(build_settings['proj_files'][proj_file]['configurations'])

                if 'default_configuration' in build_settings['proj_files'][proj_file]:
                    del(build_settings['proj_files'][proj_file]['default_configuration'])


    elif len(pkg_info['sln_files'].keys()) > 1:
        raise KeyError('more than one sln files')

    #pprint.pprint(json.dumps(build_settings))

    with open('build_settings.json', 'w') as fp:
        print(json.dumps(build_settings), file=fp)

    return build_settings


def get_build_commands(build_settings, pkg_dir):

    with open('build.sh', 'w') as fp:
        print('#! /usr/bin/env bash\n', file=fp)

        print('cd {0}'.format(pkg_dir), file=fp)

        if len(build_settings['sln_files'].keys()) == 0:
            for proj_file in build_settings['proj_files'].keys():
                proj_info = build_settings['proj_files'][proj_file]

                if 'nobuild' not in proj_info:
                    cmd = 'dotnet build {0}  --framework {1} --configuration {2}'.format(proj_file,
                                                                                         proj_info['framework'],
                                                                                         proj_info['configuration'])
                    print("(\n\t{0}\n)\n\n".format(cmd), file=fp)

        elif len(build_settings['sln_files'].keys()) == 1:
            sln_file = list(build_settings['sln_files'].keys())[0]
            for proj_file in build_settings['sln_files'][sln_file]:
                proj_info = build_settings['proj_files'][proj_file]
                if 'nobuild' not in proj_info:
                    cmd = 'dotnet build {0}  --framework {1} --configuration {2}'.format(proj_file,
                                                                                         proj_info['framework'],
                                                                                         proj_info['configuration'])
                    print("(\n\t{0}\n)\n\n".format(cmd), file=fp)



def get_build_settings_and_commands(json_file, pkg_dir):
    build_settings = get_build_settings(json_file, pkg_dir)

    get_build_commands(build_settings, pkg_dir)



