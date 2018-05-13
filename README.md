# Jenkins-Reviewboard Bot
# Overview
This tool allows a reviewboard review request being posted against a perforce
depot to trigger a jenkins build of the diff.

# Reqirements
- Linux environment to run the proxy
- Python 2.7 with virtualenv available.
- Other dependencies are installed

# Usage
## Installation
- clone the git repo locally
```
git clone <path to repo>
```
- It is recommend to deploy the application within a virtualenv. Establish one.
```
mkdir jrbbinstall
cd jrbbinstall
virtualenv .
```
- Activate the virtualenv and install the python package from your local copy
```
source bin/activate
pip install <path to local copy of git repo>
```

## Configuration

### Tools
The tools require authentication information and settings to be configured

- Copy the jrbb.config.template file
- Edit with your favourite editor and fill in each setting (all are
  mandatory)

### Reviewboard server
Configure a web hook
- URL:  http://<proxy url>:<proxy port>/post
- Encoding: Form data
- "Use custom payload" checked
- Custom content:
```
review_url={{review_request.absolute_url}}&review_id={{review_request.id}}&review_commit_id={{review_request.commit_id}}
```

### Jenkins
Create a suitable build job. The provided pipeline provides an example of
- The parameters which are required
- Calls of scripts within the prepared virtualenv to retrieve the patch file
  and post back the build results
   - A helpful wrapper jrbb_runitwithvenv.sh simplifies this a little

## Running
The proxy service can be run from the virtualenv
```
source bin/activate
./bin/jrbb_service --cfg <path to config file>
```

# Security
- This is intended for use in a secured private network, and should not be
  exposed to the internet.
- The proxy does not authenticate access so if you don't trust users on your
  network this isn't for you.

# Architecture
- Reviewboard server webhook invokes URL on a proxy service providing
  information about the review (url, id, commit id)
- Proxy service determines if the review is targeted at a review bot user
  and if the review is for a depot area of interest.
  If the review should be built, it determines if the review's commit contains
  a shelve, before triggering the Jenkins job build with a series of parameters
- Jenkins 'build' job attempts to retrieve the changes from the review and posts
  back success or failure

## Proxy
Bottle-based "proxy" to receive webhook calls from reviewboard and forward
to jenkins with proper authentication. Reviewboard does not appear capable of
providing this authentication on a properly secured Jenkins deployment.
The proxy also filters requests to avoid excessive triggering of the build
job in Jenkins

