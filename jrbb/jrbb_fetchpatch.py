from rbtools.api.client import RBClient
import argparse
import ConfigParser
import os

def main():
    '''
    Fetches the latest patch diff from the review given the review id passed
    as a parameter and writes it to patch.diff in the current directory.
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviewid",
                        required=True,
                        help="review id to post to")
    parser.add_argument("--cfg",
                        required=True,
                        help="Configuration file")
    args = parser.parse_args()
    reviewId = args.reviewid

    config = ConfigParser.ConfigParser()

    try:
        config.read(args.cfg)

        client = RBClient(
            config.get('hookservice', 'reviewboard_server'),
            username=config.get('hookservice', 'reviewboard_user'),
            password=config.get('hookservice', 'reviewboard_password'))

    except ConfigParser.NoSectionError:
        print "Configuration file " + args.cfg + " not found or missing items"
        exit(1)

    root = client.get_root()

    # Get the revision number of the latest diff from the review
    rr = root.get_review_request(review_request_id=reviewId)
    diffRevision = rr.get_latest_diff().revision
    print "Latest diff revision for review", reviewId, "is", diffRevision
    diff = root.get_diff(review_request_id=reviewId, diff_revision=diffRevision)
    patch = diff.get_patch()

    print "Retrieved the following patch file"
    print "--------------------------------------------------------------------"
    print patch.data
    print "--------------------------------------------------------------------"

    outF = open("patch.diff", "w")
    print >>outF, patch.data
    outF.close()
    print "Patch written to patch.diff"

