"""
Fetches a patch file file from a reviewboard review and writes specified
output file
"""

import argparse
import ConfigParser
from rbtools.api.client import RBClient


def main():
    '''
    Fetches the latest patch diff from the review given the review id passed
    as a parameter and writes it an output file.
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviewid",
                        required=True,
                        help="review id to post to")
    parser.add_argument("--cfg",
                        required=True,
                        help="Configuration file")
    parser.add_argument("--out",
                        required=True,
                        help="Output file location (e.g. patch.diff)")
    args = parser.parse_args()
    reviewid = args.reviewid

    config = ConfigParser.ConfigParser()

    try:
        config.read(args.cfg)

        client = RBClient(
            config.get('jrbb', 'reviewboard_server'),
            username=config.get('jrbb', 'reviewboard_user'),
            api_token=config.get('jrbb', 'reviewboard_apitoken'))

    except ConfigParser.NoSectionError:
        print "Configuration file " + args.cfg + " not found or missing items"
        exit(1)

    root = client.get_root()

    # Get the revision number of the latest diff from the review

    # pylint: disable=no-member
    reviewrequest = root.get_review_request(review_request_id=reviewid)
    diffrevision = reviewrequest.get_latest_diff().revision
    print "Latest diff revision for review", reviewid, "is", diffrevision
    diff = root.get_diff(review_request_id=reviewid,
                         diff_revision=diffrevision)
    patch = diff.get_patch()

    print "Retrieved the following patch file"
    print "-------------------------------------------------------------------"
    print patch.data
    print "-------------------------------------------------------------------"

    outfile = open(args.out, "w")
    print >>outfile, patch.data
    outfile.close()
    print "Patch written to " + args.out
