from . import ask_db
import sys


if __name__ == '__main__':
    query = str(sys.argv[1])
    ask_db(query)
