"""
Simulates reviewboard invoking the proxy application.
(used for testing)
"""

import argparse
import requests


def main():
    """
    main entry point
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("--reviewurl", required=True, help="review url")
    parser.add_argument("--reviewid", required=True, help="review id")
    parser.add_argument("--reviewcommitid", required=True,
                        help="review commit id")
    parser.add_argument("--address", required=True,
                        help="Address and port of server (no trailing slash)")
    args = parser.parse_args()

    response = requests.post(args.address+"/post",
                             data={'review_url': args.reviewurl,
                                   'review_id': args.reviewid,
                                   'review_commit_id': args.reviewcommitid})

    print 'Response:\n' + response.text
