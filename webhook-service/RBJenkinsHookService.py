import jenkins
from bottle import Bottle, route, run, post, request

app = Bottle()

@app.post('/post')
def result():
    # Expect 3 parameters
    # job              - Name of the jenkins job to trigger
    # REVIEW_URL       - URL of review in reviewbaord
    # review_id        - The id for the review
    # review_commit_id - The "commit id" for the review
    if ('job' in request.forms and
        'REVIEW_URL' in request.forms and
        'review_id' in request.forms and
        'review_commit_id' in request.forms):

        job = request.forms['job']
        reviewUrl = request.forms['REVIEW_URL']
        reviewId = request.forms['review_id']
        reviewCommitId = request.forms['review_commit_id']
        print 'Received request\n'\
                         'job=' + job + '\n'\
                         'url=' + reviewUrl + '\n'\
                         'id=' + reviewId + 's\n'\
                         'cid=' + reviewCommitId

        try:
            server = jenkins.Jenkins(
                'http://localhost:8080',
                username='Jenkins.ReviewBot',
                password='dc446ad47c6c79fe4814f21ad594b023')

            if server.job_exists(job):
                print "job ' + job + ' exists. Attempting trigger..."
                queueItemNo = server.build_job(
                    job,
                    {'REVIEW_URL': reviewUrl,
                     'review_id': reviewId,
                     'review_commit_id': reviewCommitId})
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
    else:
        print 'ERROR: Missing parameter'
        return 'ERROR: Missing parameter'

app.run(host='localhost', port=5000, debug=True)
