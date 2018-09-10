import sys
import os.path as osp
from .dotnet_pkg_info import DotnetPackageInfo
import pprint

if __name__ == '__main__':
    dpi = DotnetPackageInfo()
    pprint.pprint(dpi.get_pkg_info(sys.argv[1]))



