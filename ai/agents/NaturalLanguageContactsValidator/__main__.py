from . import validate_contacts
import sys


if __name__ == '__main__':
    query = str(sys.argv[1])
    validate_contacts(query)
