import argparse
from backend.waypoint.backup import restore
parser=argparse.ArgumentParser();parser.add_argument('archive');parser.add_argument('destination');args=parser.parse_args()
print(restore(args.archive,args.destination))
print('Set WAYPOINT_DATA to this path before starting the server. Pair devices again.')
