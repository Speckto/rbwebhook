import jenkins
from flask import Flask
from flask import request

app = Flask(__name__)


@app.route('/post', methods=['POST'])
def result():
    # Expect 3 parameters
    # job              - Name of the jenkins job to trigger
    # REVIEW_URL       - URL of review in reviewbaord
    # review_id        - The id for the review
    # review_commit_id - The "commit id" for the review
    job = request.form['job']
    reviewUrl = request.form['REVIEW_URL']
    reviewId = request.form['review_id']
    reviewCommitId = request.form['review_commit_id']
    app.logger.info('Received request\n\
                     job=%s\n\
                     url=%s\n\
                     id=%s\n\
                     cid=%s',
                    job,
                    reviewUrl,
                    reviewId,
                    reviewCommitId)

    try:
        server = jenkins.Jenkins('http://localhost:8080',
                                 username='Jenkins.ReviewBot',
                                 password='')

        if server.job_exists(job):
            app.logger.info("job %s exists. Attempting trigger...", job)
            queueItemNo = server.build_job(
                job,
                {'REVIEW_URL': reviewUrl,
                 'review_id': reviewId,
                 'review_commit_id': reviewCommitId})
            queueItem = server.get_queue_item(queueItemNo)
        else:
            app.logger.info("ERROR: job does not exist in jenkins")
            return 'ERROR: Job does not exist in jenkins'

    except (jenkins.JenkinsException,
            jenkins.NotFoundException,
            jenkins.EmptyResponseException,
            jenkins.BadHTTPException,
            jenkins.TimeoutException) as error:
        app.logger.info('Error interacting with Jenkins - error was:\n', error)
        return 'ERROR: Failed to trigger:' + error

    else:
        app.logger.info('OK: Job triggered')
        return 'OK: Job triggered'
