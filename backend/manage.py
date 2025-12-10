#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# Fix for Windows HTTP/2 socket issues - must be set before httpx is imported
if sys.platform == 'win32':
    os.environ['HTTPX_HTTP2'] = '0'
    os.environ['HTTPCORE_HTTP2'] = '0'


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
