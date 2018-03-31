#!/usr/bin/python
# Work out if the change number is a perforce change and contains shelved files.
# We're going to want to prefer using a shelve over applying the diff as file
# moves don't work right with patch
from P4 import P4,P4Exception    # Import the module
import os

shelvedChange = False
changeNo = os.environ["review_commit_id"]

if changeNo != "" and changeNo.isdigit():
    p4 = P4()
    p4.port = "1666"
    p4.user = "Neil.Potter"

    try:                               # Catch exceptions with try/except
        p4.connect()                   # Connect to the Perforce server
        desc = p4.run("describe","-S",changeNo) # Run "p4 info" (returns a dict)
        p4.disconnect()                # Disconnect from the server
    except P4Exception:
        print "Error occurred"
        for e in p4.errors:            # Display errors
            print e

    for e in desc:
        if e.has_key('shelved'):
            shelvedChange = True
            break
else:
    print "Change number '"+changeNo+"'"\
          "doesn't look like a perforce change number"
    shelvedChange = False

if shelvedChange == True:
    print "Shelved change - exiting with code 0"
    exit(0)
else:
    print "Shelved change not detected - exiting with code 1"
    exit(1)

# Write environment properties file. This allows a conditional build step
# to work out the result of running this script
#outF = open("IsShelveResult.properties", "w")
#if shelvedChange == True:
#    print "review commit id of",changeNo,"is a shelved change"
#    print >>outF,"IS_SHELVED_CHANGE=1"
#else:
#    print "review commit id of",changeNo,"is not a shelved change"
#    print >>outF,"IS_SHELVED_CHANGE=0"
#
#outF.close()

