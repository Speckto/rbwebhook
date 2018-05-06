#!/usr/bin/python
#
# Determines if the review given the review id provided by parameter
# is relevant to the reviewbot.

from rbtools.api.client import RBClient
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--reviewid", required=True, help="review id to post to")
parser.add_argument("--depotpath", required=True,
                    help="Depot path considered relevant")
args = parser.parse_args()
reviewId = args.reviewid
depotPath = args.depotpath

client = RBClient('http://127.0.0.1/',
                  username='Jenkins.Reviewbot',
                  password='useruserrb')
root = client.get_root()

reviewRequest = root.get_review_request(review_request_id=reviewId)

relevantFiles = False
reviewForBot = False
for p in reviewRequest.target_people:
    if p.title == "Jenkins.Reviewbot":
        print "Review is addressed to the review bot"
        reviewForBot = True
        break

# check file paths are in mainline
for line in open("patch.diff"):
    if (line.startswith("--- " + depotPath) or
       line.startswith("+++ " + depotPath)):
        print "Review diff contains files for relevant product"
        relevantFiles = True
        break

if relevantFiles and reviewForBot:
    print "This review is relevant (exit code=0)"
    exit(0)
else:
    print "Review is not relevant (exit code=1)"
    exit(1)

