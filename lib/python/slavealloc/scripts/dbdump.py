import cPickle
import sys
from slavealloc.data import model

def setup_argparse(subparsers):
    subparser = subparsers.add_parser('dbdump', help="""dump the slavealloc
            database to a file suitable for use with dbinit""")

    subparser.add_argument('dumpfile', nargs='?',
            help="""filename to dump to; default is standard output""")

    return subparser

def process_args(subparser, args):
    pass

# DATA FORMAT
#
# This format is meant to support debugging dumps of the database, and not for
# long-term storage, so there is no provision for versioning -- as the db
# schema changes, the file format wil change.
#
# The file contains a single pickled dictionary with keys for each table.  Each
# key points to a list of rows in a format suitable for use with insert().

def main(args):
    def dump_tbl(table):
        res = table.select().execute()
        return [ dict(row) for row in res ]
    rv = dict( (tname, dump_tbl(tbl)) for (tname, tbl) in model.metadata.tables.items() )

    output = sys.stdout
    if args.dumpfile:
        output = open(args.dumpfile, "w")
    cPickle.dump(rv, output)
