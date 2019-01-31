#!/usr/bin/env python3

# Internal
import sys
from itertools import chain
from configparser import ConfigParser


def read_config(file, ctx, prop):
    parser = ConfigParser()
    with open(file, encoding="utf8") as config_file:
        fixed_config_file = chain(("[__TOP__]",), config_file)
        parser.read_file(fixed_config_file)

    return parser.get(ctx, prop, fallback="")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Missing arguments", file=sys.stderr)
        sys.exit(-1)

    print(read_config(sys.argv[1], sys.argv[2], sys.argv[3]))
