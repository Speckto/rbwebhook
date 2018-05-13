# Jenkins-Reviewboard Bot
# Introduction
This tool is a tool of pipelines for allowing reviewboard reviews to
to trigger a Jenkins job which builds the changes.

Intended to be triggered from a reviewboard web-hook, this attempts to filter
calls to specific areas of a perforce depot triggering a Jenkins job
for applicable reviews.

Where perforce is being used as the source control system, a shelved change
will be unshelved, falling back to applying the diff fetched from reviewboard
directly (the diff doesn't deal with perforce moved files very well). The
latter allows use with git-p4.

# Status
- Scripts work
- Pipelines work
- Use reviewboard webhooks to trigger Jenkins jobs is proving to be problematic
- This is intended for use in a secured private network, and should not be
  exposed to the internet.

# Architecture
- Reviewboard server webhook invokes URL on a proxy service providing
  information about the review (url, id, commit id)
- Proxy service determines if the review is targetted at a review bot user
  and if the review is for a depot area of interest.
  If the review should be built, it determines if the review's commit contains
  a shelve, before triggering the jenkins job build with a series of parameters
- Jenkins 'build' job attempts to retrieve the changes from the review and posts
  back success or failure

## Proxy
Bottle-based "proxy" to receive webhook calls from reviewboard and forward
to jenkins with proper authentication. Reviewboard does not appear capable of
providing this authentication on a properly secured Jenkins deployment.
The proxy also filters requests to avoid excessive triggering of the build
job in Jenkins

# Reviewboard server configuration
Configure a web hook
- URL:  http://<proxy url>:<proxy port>/post
- Encoding: Form data
- "Use custom payload" checked
- Custom content:
```
job=MMA-main-reviewbot-build-pipeline&REVIEW_URL={{review_request.absolute_url}}&review_id={{review_request.id}}&review_commit_id={{review_request.commit_id}}
```

# Task list
- The interface between some scripts and the Jenkins pipeline is currently
  shell exit codes which is rather clunky
- Bottle application needs better packaging
- Provide deployment scripts for bottle application (use uWSGI?)
- Read configuration file containing settings, etc

