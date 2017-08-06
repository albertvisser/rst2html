#! /usr/bin/env python3
"""Startup script for previewing a markdown document
"""
import sys
from tohtml.frommd import main
main(sys.argv[1] if len(sys.argv) > 1 else '')
