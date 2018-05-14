import jenkins
from rbtools.api.client import RBClient
from bottle import Bottle, route, run, post, request
from P4 import P4, P4Exception
import argparse
import re
import itertools

app = Bottle()

depotPaths = dict()

def ReviewCommitHasShelve(cfg, reviewCommitId):
    """
    Determines if the specified commit id (usually a git hash or a perforce
    change has a perforce change.
    """
    shelvedChange = False
    if reviewCommitId != "" and reviewCommitId.isdigit():
        p4 = P4()
        p4.port = cfg['jrbb.perforce_port']
        p4.user = cfg['jrbb.perforce_user']

        try:
            p4.connect()
            # Run "p4 info" (returns a dict)
            desc = p4.run("describe", "-S", reviewCommitId)
            p4.disconnect()
        except P4Exception as p4e:
            print "Error occurred interrogating shelve -\
                  listing error messages"
            print p4e
            # Sometimes p4.errors is empty even though it should not be...
            for e in p4.errors:
                print e
            print "Error occurred - cannot determine if this is a shelve"
            shelvedChange = False

        for e in desc:
            if 'shelved' in e:
                shelvedChange = True
                break
    else:
        print "Review commit '"+reviewCommitId+"'"\
              "doesn't look like a perforce change number"
        shelvedChange = False

    if shelvedChange:
        print "Review commit " + reviewCommitId + " is a shelved change."
    else:
        print "Review commit " + reviewCommitId + " is not a shelved change."
    return shelvedChange

def GetJob(line):
    for path in depotPaths:
        job = depotPaths[path]
        if (line.startswith("--- " + path) or
            line.startswith("+++ " + path)):
            return job
    # None found
    return ""

def ReviewRelevant(cfg, reviewId):
    """
    Determines if a review is relevant to the bot. Checks if it is
    address to the bot and if the diff alters the specified depot path.
    Returns a dict indicating if it is relevant to to the build and validator
    bot.
    """

    # Only interested in reviews addressed to the bot
    client = RBClient(cfg['jrbb.reviewboard_server'],
                      username=cfg['jrbb.reviewboard_user'],
                      password=cfg['jrbb.reviewboard_password'])
    root = client.get_root()

    reviewRequest = root.get_review_request(review_request_id=reviewId)

    hasDiff = False
    relevantFiles = False
    reviewForBuildBot = False
    reviewForValidatorBot = False
    for p in reviewRequest.target_people:
        if p.title == cfg['jrbb.reviewboard_user']:
            print "Build bot is review recipient."
            reviewForBuildBot = True
        elif 'jrbb_validator.validator_reviewboard_user' in cfg and\
             p.title == cfg['jrbb_validator.validator_reviewboard_user']:
            print "Validator bot is review recipient."
            reviewForValidatorBot = True

    if reviewForBuildBot or reviewForValidatorBot:
        try:
            latestDiff = reviewRequest.get_latest_diff()
            hasDiff = True
        except AttributeError:
            hasDiff = False

        if hasDiff:
            diffRevision = latestDiff.revision
            diff = root.get_diff(review_request_id=reviewId,
                                 diff_revision=diffRevision)
            patch = diff.get_patch()

            for line in patch.data.splitlines():
                jobName = GetJob(line)
                if jobName != "":
                    print "Review diff contains files for " + jobName
                    relevantFiles = True
                    break

            if not relevantFiles:
                print "Review diff does not contain files for relevant product"
        else:
            print "Review has no diff so is not for the bot"
    else:
        print "Review is not addressed to either bot"

    # The validator can run on anything with a diff addressed to it
    # The normal build bot requires diff in a supported depot path
    ret = {'reviewForBuildBot': (reviewForBuildBot and relevantFiles),
           'reviewForValidatorBot': (reviewForValidatorBot and hasDiff),
           'buildBotJob': jobName}
    print "Relevant to build bot    : " + str(ret['reviewForBuildBot'])
    print "Build bot job            : " + ret['buildBotJob']
    print "Relevant to validator bot: " + str(ret['reviewForValidatorBot'])
    return ret

def KickJenkinsJob(cfg,
                   job,
                   reviewUrl,
                   reviewId,
                   reviewCommitId,
                   shelvedChange):
    """
    Kicks off a build of a jenkins job with the specified parameters
    """
    try:
        server = jenkins.Jenkins(
            cfg['jrbb.jenkins_server'],
            username=cfg['jrbb.jenkins_user'],
            password=cfg['jrbb.jenkins_apikey'])

        if server.job_exists(job):
            print 'job ' + job + ' exists. Attempting trigger...'
            queueItemNo = server.build_job(
                job,
                {'REVIEW_URL': reviewUrl,
                 'review_id': reviewId,
                 'review_commit_id': reviewCommitId,
                 'use_shelve': ('true' if shelvedChange else 'false')})
            queueItem = server.get_queue_item(queueItemNo)
        else:
            print 'ERROR: job does not exist in jenkins'
            return 'ERROR: Job does not exist in jenkins'

    except (jenkins.JenkinsException,
            jenkins.NotFoundException,
            jenkins.EmptyResponseException,
            jenkins.BadHTTPException,
            jenkins.TimeoutException) as error:
        print 'Error interacting with Jenkins - error was:\n' + error
        return 'ERROR: Failed to trigger:' + error

    else:
        print 'OK: Job triggered'
        return 'OK: Job triggered'

@app.post('/post')
def result():
    """
    Handle post containing these parameters
    @param review_url:       URL of review in reviewbaord
    @param review_id:        The id for the review
    @param review_commit_id: The "commit id" for the review
    """
    cfg = request.app.config
    if ('review_url' in request.forms and
        'review_id' in request.forms and
        'review_commit_id' in request.forms):

        reviewUrl = request.forms['review_url']
        reviewId = request.forms['review_id']
        reviewCommitId = request.forms['review_commit_id']
        print '>>> Received request\n'\
                         '    url=' + reviewUrl + '\n'\
                         '    id=' + reviewId + '\n'\
                         '    cid=' + reviewCommitId

        rel = ReviewRelevant(cfg,
                             reviewId)

        if rel['reviewForBuildBot'] == True:
            shelvedChange = ReviewCommitHasShelve(cfg, reviewCommitId)

            return KickJenkinsJob(cfg,
                                  rel['buildBotJob'],
                                  reviewUrl,
                                  reviewId,
                                  reviewCommitId,
                                  shelvedChange)

        if rel['reviewForValidatorBot'] == True:
            print "TODO: Invoke the validator bot"

    else:
        print 'ERROR: Missing parameter'
        return 'ERROR: Missing parameter'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cfg",
                        required=True,
                        help="Configuration file")
    args = parser.parse_args()

    app.config.load_config(args.cfg)

    # Mandatory parameters
    for opt in [
                'jrbb.server_host',
                'jrbb.server_port',
                'jrbb.perforce_port',
                'jrbb.perforce_user',
                'jrbb.jenkins_server',
                'jrbb.jenkins_user',
                'jrbb.jenkins_apikey',
                'jrbb.reviewboard_server',
                'jrbb.reviewboard_user',
                'jrbb.reviewboard_password',
                'jrbb.paths_to_jobs',
               ]:
        if not opt in app.config:
            print "Error: Configuration is missing option " + opt
            exit(1)

    # Extract job to depot path mappings from config
    l = app.config['jrbb.paths_to_jobs'].split()
    for path, job in zip(l[0::2], l[1::2]):
        depotPaths[path] = job

    if not depotPaths:
        print "No depot path to job mappings defined"
        exit(1)
    else:
        print "Depot path mappings"
        for key in depotPaths:
            print "   " + key + " = " + depotPaths[key]

    print "Application configuration:"
    print app.config
    app.run(host=app.config['jrbb.server_host'],
            port=app.config['jrbb.server_port'],
            debug=True)
