# Jenkins-Reviewboard "Review bot"
# Introduction
This tool is a series of pipelines for allowing reviewboard reviews to
to trigger a Jenkins job which builds the changes.

Intended to be triggered from a reviewboard web-hook, this attempts to filter
calls to specific areas of a perforce depot.

Where perforce is being used as the source control system, a shelved change
will be unshelved, falling back to applying the diff fetched from reviewboard
directly (the diff doesn't deal with perforce moved files very well).

# Status
- Scripts work
- Pipelines work
- Use reviewboard webhooks to trigger Jenkins jobs is proving to be problematic

# TODO
- The interface between some scripts and the Jenkins pipeline is currently
  shell exit codes which is rather clunky

