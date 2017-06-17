#! /usr/bin/env python3
import sys
from htmlfromrst import main
main(sys.argv[1] if len(sys.argv) > 1 else '')
