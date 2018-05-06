#!/usr/bin/python
# Work out if the change number is a perforce change and contains shelved
# files.
# We're going to want to prefer using a shelve over applying the diff as file
# moves don't work right with patch
from P4 import P4, P4Exception
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--reviewcommitid", required=True,
                    help="review commit id - so a change or git hash")

args = parser.parse_args()
changeNo = args.reviewcommitid

shelvedChange = False
if changeNo != "" and changeNo.isdigit():
    p4 = P4()
    p4.port = "1666"
    p4.user = "Neil.Potter"

    try:
        p4.connect()
        # Run "p4 info" (returns a dict)
        desc = p4.run("describe", "-S", changeNo)
        p4.disconnect()
    except P4Exception as p4e:
        print "Error occurred - listing error messages"
        print p4e
        # Sometimes p4.errors is empty even though it should not be...
        for e in p4.errors:            # Display errors
            print e
        print "--"
        print "Cannot determine if this is a shelve"
        # Raise this to the caller (crash)
        raise

    for e in desc:
        if 'shelved' in e:
            shelvedChange = True
            break
else:
    print "Change number '"+changeNo+"'"\
          "doesn't look like a perforce change number"
    shelvedChange = False

# TODO: This is a rubbish interface. Needs revision
if shelvedChange:
    print "Shelved change - exiting with code 0"
    exit(0)
else:
    print "Shelved change not detected - exiting with code 1"
    exit(1)

