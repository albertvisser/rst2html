#! /usr/bin/env python3
import sys
from tohtml.frommd import main
main(sys.argv[1] if len(sys.argv) > 1 else '')
