#!/usr/bin/python
#
# Simulates reviewboard invoking the proxy application
#
import argparse
import requests

parser = argparse.ArgumentParser()
parser.add_argument("--reviewurl", required=True, help="review url")
parser.add_argument("--reviewid", required=True, help="review id")
parser.add_argument("--reviewcommitid", required=True, help="review commit id")
args = parser.parse_args()

r = requests.post("http://localhost:5000/post",
                  data={'review_url': args.reviewurl,
                        'review_id': args.reviewid,
                        'review_commit_id': args.reviewcommitid})

print 'Response:\n' + r.text
