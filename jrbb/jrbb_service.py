from rbtools.api.client import RBClient
from bottle import Bottle, route, run, post, request
from P4 import P4, P4Exception
from waitress import serve
import jenkins
import requests
import argparse
import pprint


app = Bottle()

# Maps depot paths to Jenkins jobs which build that path.
# This is constant once initialised by main.
gDepotPaths = dict()


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


def GetJobForLine(depotPaths, line):
    """
    Interprets a line of a diff (patch format) looking for affected files.
    If a file header statement has a perforce path matching one of the paths
    relevant to a Jenkins job, returns that job.

    @param depotPaths Dict mapping perforce paths to a jenkins job
    @param line       A line from a diff to examine
    @return "" if the line has no associated job
            A Jenkins job name if patch line is a file header with a path
            matching the pattern for a job
    """
    for path in depotPaths:
        job = depotPaths[path]
        if (line.startswith("--- " + path) or line.startswith("+++ " + path)):
            return job
    # None found
    return ""


def ReviewRelevant(cfg, depotPaths, reviewId):
    """
    Determines if a review is relevant to the bot. Checks if it is
    address to the bot and if the diff alters the specified depot path.
    Returns a dict indicating if it is relevant to to the build and validator
    bot.
    """

    # Only interested in reviews addressed to the bot
    client = RBClient(cfg['jrbb.reviewboard_server'],
                      username=cfg['jrbb.reviewboard_user'],
                      api_token=cfg['jrbb.reviewboard_apitoken'])
    root = client.get_root()

    reviewRequest = root.get_review_request(review_request_id=reviewId)

    haveValidatorBot = 'jrbb_validator.validator_reviewboard_user' in cfg
    hasDiff = False
    relevantFiles = False
    reviewForBuildBot = False
    reviewForValidatorBot = False
    buildBotName = cfg['jrbb.reviewboard_user']
    validatorBotName = ''
    jobName = ''
    if haveValidatorBot:
        validatorBotName = cfg['jrbb_validator.validator_reviewboard_user']

    # Determine if either bot has been directly targeted in the review
    for p in reviewRequest.target_people:
        reviewForBuildBot = reviewForBuildBot or (p.title == buildBotName)
        reviewForValidatorBot = \
            reviewForValidatorBot or (p.title == validatorBotName)
        if reviewForValidatorBot and reviewForBuildBot:
            break

    # If either user cannot be found as a target person we have to check
    # if they are within any of the groups
    if (not reviewForBuildBot) or (haveValidatorBot and not
                                   reviewForValidatorBot):
        for tg in reviewRequest.target_groups:
            group = tg.get()
            # You are supposed to be able to filter users using q=name but that
            # doesn't seem to work
            groupUsers = group.get_review_group_users()
            for u in groupUsers:
                reviewForBuildBot = reviewForBuildBot or\
                                        u.username == buildBotName
                reviewForValidatorBot = \
                    reviewForValidatorBot or u.username == validatorBotName

            if reviewForValidatorBot and reviewForBuildBot:
                break

    print "Review people status: for build bot=" + str(reviewForBuildBot) +\
          ", for validator bot=" + str(reviewForValidatorBot)

    # This is addressed to one of the bots, so now work out if there is a diff
    # and if said diff is of interest
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
                jobName = GetJobForLine(depotPaths, line)
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
    @return 0 on failure, 1 on success
    """
    try:
        server = jenkins.Jenkins(
            cfg['jrbb.jenkins_server'],
            username=cfg['jrbb.jenkins_user'],
            password=cfg['jrbb.jenkins_apikey'])

        if server.job_exists(job):
            params = {'REVIEW_URL': reviewUrl,
                      'review_id': reviewId,
                      'review_commit_id': reviewCommitId,
                      'use_shelve': ('true' if shelvedChange else 'false')}
            print 'Trigger job ' + job + ' with parameters:'
            pprint.pprint(params)
            server.build_job(job, params)
        else:
            print 'ERROR: job does not exist in jenkins'
            return 0

    except (jenkins.JenkinsException,
            jenkins.NotFoundException,
            jenkins.EmptyResponseException,
            jenkins.BadHTTPException,
            jenkins.TimeoutException) as error:
        print 'Error interacting with Jenkins - error was:\n' + error
        return 0

    else:
        print 'OK: Build job triggered'
        return 1


@app.post('/post')
def result():
    """
    Handle post containing these parameters
    @param review_url:       URL of review in reviewbaord
    @param review_id:        The id for the review
    @param review_commit_id: The "commit id" for the review
    """
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

        rel = ReviewRelevant(request.app.config,
                             gDepotPaths,
                             reviewId)

        if rel['reviewForBuildBot']:
            shelvedChange = ReviewCommitHasShelve(request.app.config,
                                                  reviewCommitId)

            KickJenkinsJob(request.app.config,
                           rel['buildBotJob'],
                           reviewUrl,
                           reviewId,
                           reviewCommitId,
                           shelvedChange)

        if rel['reviewForValidatorBot']:
            # TODO: Test this, with the exact parameters names, etc
            url = request.app.config['jrbb_valiator.validator_url']
            print "Invoke validator bot at: " + url
            secret = request.app.config['jrbb_validator.validator_secret']
            data = {'key': secret,
                    'reviewId': reviewId}
            resp = requests.post(url, params=data)
            print "Response is: code=" + resp.status_code + " Msg=" + resp.text

        return "OK"
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
                'jrbb.reviewboard_apitoken',
                'jrbb.paths_to_jobs',
               ]:
        if opt not in app.config:
            print "Error: Configuration is missing option " + opt
            exit(1)

    # Extract job to depot path mappings from config
    jobPaths = app.config['jrbb.paths_to_jobs'].split()
    for path, job in zip(jobPaths[0::2], jobPathsl[1::2]):
        gDepotPaths[path] = job

    if not gDepotPaths:
        print "No depot path to job mappings defined"
        exit(1)
    else:
        print "Depot path mappings"
        for key in gDepotPaths:
            print "   " + key + " = " + gDepotPaths[key]
        print ""

    print "Application configuration:"
    pprint.pprint(app.config)
    print ""
    serve(app,
          host=app.config['jrbb.server_host'],
          port=app.config['jrbb.server_port'])
