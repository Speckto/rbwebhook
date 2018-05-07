# Jenkins-Reviewboard "Review bot"
# Introduction
This tool is a series of pipelines for allowing reviewboard reviews to
to trigger a Jenkins job which builds the changes.

Intended to be triggered from a reviewboard web-hook, this attempts to filter
calls to specific areas of a perforce depot.

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
- Proxy service forwards request Jenkins server, starting a build of a
  jenkins job with parameters provided by reviewboard server
- "callback" pipeline job in Jenkins receives request and identifies if it is
  related to the perforce server area of interest.
  If it is, invokes a build job
- 'build' job which attempts to retrieve the changes from the review and posts
  back success or failure
## Proxy
Flask-based "proxy" to receive webhook calls from reviewboard and forward
to jenkins with proper authentication. Reviewboard does not appear capable of
providing this authentication on a properly secured Jenkins deployment.

# Reviewboard server configuration
Configure a web hook
- URL:  http://<proxy url>:<proxy port>/post
- Encoding: Form data
- "Use custom payload" checked
- Custom content:
```
job=MMA-main-reviewbot-callback-pipeline&REVIEW_URL={{review_request.absolute_url}}&review_id={{review_request.id}}&review_commit_id={{review_request.commit_id}}
```

# Proxy
A python "Flask" based microservice application is provided.
Deploy this using your favourite microservice server.

# TODO
- The interface between some scripts and the Jenkins pipeline is currently
  shell exit codes which is rather clunky
- Flask application needs better packaging
- Provide deployment scripts for flask application (use uWSGI?)

