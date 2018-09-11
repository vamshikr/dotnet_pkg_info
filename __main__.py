import sys
import pprint
import argparse
from .dotnet_pkg_info import DotnetPackageInfo
import json


def process_cli_args():

    cli_parser = argparse.ArgumentParser(prog='dotnet_pkg_info',
                                         description='''Use any of the sub commands''')

    cli_parser.add_argument('--package',
                            required=True,
                            help='gets the version of the program')

    cli_parser.add_argument('--format',
                            choices=['json', 'text'],
                            default='json',
                            required=False,
                            help='gets the version of the program')

    return cli_parser.parse_args()


def pprint(indent, value):
    print('{indent}{value}'.format(indent=' '*indent, value=value))


def pretty_print(pkg_info, indent=4):

    curr_indent = 0
    for tag in pkg_info.keys():
        pprint(curr_indent, tag)

        curr_indent = curr_indent + 4

        if tag == DotnetPackageInfo.SLN_FILES_TAG:
            for sln_file in pkg_info[DotnetPackageInfo.SLN_FILES_TAG].keys():
                pprint(curr_indent, sln_file)
        else:
            for proj_file in pkg_info[DotnetPackageInfo.PROJ_FILES_TAG].keys():
                pprint(curr_indent, proj_file)

                next_indent = curr_indent + 4
                for _key in pkg_info[DotnetPackageInfo.PROJ_FILES_TAG][proj_file].keys():
                    pprint(next_indent, _key)

                    next_indent2 = next_indent + 4
                    if type(pkg_info[DotnetPackageInfo.PROJ_FILES_TAG][proj_file][_key]) == list:
                        for _item in pkg_info[DotnetPackageInfo.PROJ_FILES_TAG][proj_file][_key]:
                            pprint(next_indent2, _item)
                    else:
                        pprint(next_indent2, pkg_info[DotnetPackageInfo.PROJ_FILES_TAG][proj_file][_key])

        curr_indent = curr_indent - 4

if __name__ == '__main__':
    parser = process_cli_args()
    args = vars(parser)

    dpi = DotnetPackageInfo()
    pkg_info = dpi.get_pkg_info(args['package'])

    if args['format'] == 'json':
        json.dump(pkg_info, sys.stdout)
    else:
        pretty_print(pkg_info)


