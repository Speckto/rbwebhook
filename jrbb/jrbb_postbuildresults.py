from rbtools.api.client import RBClient
import argparse
import ConfigParser, os

def main():
    '''
    Posts a review to the review with specified id indicating if the build
    passed or failed
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviewid",
                        required=True,
                        help="review id to post to")
    parser.add_argument("--buildurl",
                        required=True,
                        help="The jenkins build url")
    parser.add_argument("--buildstate",
                        required=True,
                        choices=["SUCCESS", "UNSTABLE", "FAILURE"],
                        help="Indicates if build succeeded (1) or failed (0)")

    args = parser.parse_args()

    reviewId = args.reviewid
    buildUrl = args.buildurl
    buildState = args.buildstate

    config = ConfigParser.ConfigParser()

    config.read(
        '/home/vagrant/jenkinsreviewbot/jrb.config')

    client = RBClient(
        config.get('hookservice', 'reviewboard_server'),
        username=config.get('hookservice', 'reviewboard_user'),
        password=config.get('hookservice', 'reviewboard_password'))
    root = client.get_root()

    # Get the revision number of the latest diff from the review
    rr = root.get_review_request(review_request_id=reviewId)

    reviews = rr.get_reviews()

    if buildState == 'SUCCESS':
        msg = 'Successfully built changes. See ' + buildUrl
    else:
        msg = 'Opps! I could not build these changes. See ' + buildUrl

    reviews.create(body_bottom=msg,
                   public=True)

    print "Posted to review " + reviewId + " build state=" + buildState + \
           ". Build url=" + buildUrl

