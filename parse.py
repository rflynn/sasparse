
from sasparse import SASDoc


if __name__ == '__main__':

    import sys

    inputfile = sys.stdin
    if sys.argv[1:]:
        inputfile = open(sys.argv[1])

    sys.setrecursionlimit(3000)

    doc = SASDoc.from_fd(inputfile)
    from pprint import pprint
    pprint(doc.top, width=1)
    # print(doc.format(None))
