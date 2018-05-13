import jenkins
from rbtools.api.client import RBClient
from bottle import Bottle, route, run, post, request
from P4 import P4, P4Exception
import argparse

app = Bottle()

def ReviewCommitHasShelve(cfg, reviewCommitId):
    """
    Determines if the specified commit id (usually a git hash or a perforce
    change has a perforce change.
    """
    shelvedChange = False
    if reviewCommitId != "" and reviewCommitId.isdigit():
        p4 = P4()
        p4.port = cfg['hookservice.perforce_port']
        p4.user = cfg['hookservice.perforce_user']

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

def ReviewRelevant(cfg, reviewId):
    """
    Determines if a review is relevant to the bot. Checks if it is
    address to the bot and if the diff alters the specified depot path
    """

    # Only interested in reviews addressed to the bot
    client = RBClient(cfg['hookservice.reviewboard_server'],
                      username=cfg['hookservice.reviewboard_user'],
                      password=cfg['hookservice.reviewboard_password'])
    root = client.get_root()

    reviewRequest = root.get_review_request(review_request_id=reviewId)

    relevantFiles = False
    reviewForBot = False
    for p in reviewRequest.target_people:
        if p.title == cfg['hookservice.reviewboard_user']:
            print "Review is addressed to the review bot."
            reviewForBot = True
            break

    if reviewForBot:
        diffRevision = reviewRequest.get_latest_diff().revision
        diff = root.get_diff(review_request_id=reviewId,
                             diff_revision=diffRevision)
        patch = diff.get_patch()

        depotPath = cfg['hookservice.depot_path_prefix']
        for line in patch.data.splitlines():
            if (line.startswith("--- " + depotPath) or
               line.startswith("+++ " + depotPath)):
                print "Review diff contains files for relevant product"
                relevantFiles = True
                break

        if not relevantFiles:
            print "Review diff does not contain files for relevant product"
    else:
        print "Review is not addressed to the review bot."

    return (reviewForBot and relevantFiles)

def KickJenkinsJob(cfg, job, reviewUrl, reviewId, reviewCommitId, shelvedChange):
    """
    Kicks off a build of a jenkins job with the specified parameters
    """
    try:
        server = jenkins.Jenkins(
            cfg['hookservice.jenkins_server'],
            username=cfg['hookservice.jenkins_user'],
            password=cfg['hookservice.jenkins_apikey'])

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

        job = cfg['hookservice.jenkins_job_name']
        reviewUrl = request.forms['review_url']
        reviewId = request.forms['review_id']
        reviewCommitId = request.forms['review_commit_id']
        print '>>> Received request\n'\
                         '    url=' + reviewUrl + '\n'\
                         '    id=' + reviewId + 's\n'\
                         '    cid=' + reviewCommitId

        if ReviewRelevant(cfg,
                          reviewId):
            shelvedChange = ReviewCommitHasShelve(cfg, reviewCommitId)

            return KickJenkinsJob(cfg,
                                  job,
                                  reviewUrl,
                                  reviewId,
                                  reviewCommitId,
                                  shelvedChange)
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

    for opt in [
                'hookservice.server_host',
                'hookservice.server_port',
                'hookservice.perforce_port',
                'hookservice.perforce_user',
                'hookservice.jenkins_server',
                'hookservice.jenkins_user',
                'hookservice.jenkins_apikey',
                'hookservice.reviewboard_server',
                'hookservice.reviewboard_user',
                'hookservice.reviewboard_password',
                'hookservice.depot_path_prefix',
                'hookservice.jenkins_job_name',
               ]:
        if not opt in app.config:
            print "Error: Configuration is missing option " + opt
            exit(1)

    print "Application configuration:"
    print app.config
    app.run(host=cfg['hookservice.server_host'],
            port=cfg['hookservice.server_port'],
            debug=True)
