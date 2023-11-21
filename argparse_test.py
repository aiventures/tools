""" simple argparse for testing """

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-t","--test", help="sample test argument")
parser.add_argument("-p", "--param", action="store_true",
                    help="sample parameter")
args = parser.parse_args()
if args.test:
    print(f"PARSED ARG test {args.test}")
else:
    print("No test ARG")

if args.param:
    print("Flag param was set")
else:
    print("No Flag set")
