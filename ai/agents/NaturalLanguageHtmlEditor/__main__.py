from . import nlhtml_editor
import sys


if __name__ == '__main__':
    query = str(sys.argv[1])
    nlhtml_editor(query)
