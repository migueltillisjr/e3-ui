from . import route_ai_request
import sys


if __name__ == '__main__':
    query = str(sys.argv[1])
    route_ai_request(query)
