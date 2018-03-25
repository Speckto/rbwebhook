#!/usr/bin/python
# Determines if the review given by environment variable "review_id"
# is relevant to the reviewbot.
# It is expected that this environment variable is the parameter to the
# jenkins job which contains the id (not url) of the review

import os
from rbtools.api.client import RBClient

reviewId = os.environ["review_id"]

client = RBClient('http://127.0.0.1/',
                  username='Jenkins.Reviewbot',password='useruserrb')
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
    if (line.starts_with("--- //depot/MMA/main/") or
        line.starts_with("+++ //depot/MMA/main/")):
        print "Review diff contains files for relevant product"
        relevantFiles = True
        break

if relevantFiles == True and reviewForBot == True:
    print "This review is relevant"
    exit(0)
else:
    print "Review is not relevant"
    exit(1)

