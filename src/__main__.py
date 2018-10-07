
import sys
import argparse
from dotnet_pkg_info.dotnet_pkg import main
import json


if __name__ == '__main__':
    pkg_info = main(sys.argv[1])
    print(json.dumps(pkg_info.to_json()))


