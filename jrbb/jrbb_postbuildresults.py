"""
Posts a message to a review
"""

import argparse
import ConfigParser
from rbtools.api.client import RBClient


def main():
    '''
    Posts a review to the review with specified id indicating if the build
    passed or failed
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("--cfg",
                        required=True,
                        help="Configuration file")
    parser.add_argument("--reviewid",
                        required=True,
                        help="Review id to post to")
    parser.add_argument("--buildurl",
                        required=True,
                        help="The jenkins build url")
    parser.add_argument("--buildstate",
                        required=True,
                        choices=["SUCCESS", "UNSTABLE", "FAILURE"],
                        help="Indicates if build succeeded (1) or failed (0)")

    args = parser.parse_args()

    reviewid = args.reviewid
    buildurl = args.buildurl
    buildstate = args.buildstate

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
    reviewreq = root.get_review_request(review_request_id=reviewid)

    reviews = reviewreq.get_reviews()

    if buildstate == 'SUCCESS':
        msg = 'Successfully built changes. See ' + buildurl
    else:
        msg = 'Opps! I could not build these changes. See ' + buildurl

    reviews.create(body_bottom=msg, public=True)

    print "Posted to review " + reviewid + " build state=" + buildstate + \
          ". Build url=" + buildurl
