#!/usr/bin/env python
# Management utility for LatchPress.
import os
import sys

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "latchpress.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
