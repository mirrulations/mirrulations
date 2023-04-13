'use strict';

const BASE_URL = window.location.href;
const RADIUS = 80;
const NUMBER_ANIMATION_STEP = 4;

window.addEventListener('load', function init() {
    if (window.location.pathname === '/') {
        updateClientDashboardData();
        setInterval(updateClientDashboardData, 5000);
    } else if (window.location.pathname === '/dev') {
        updateDeveloperDashboardData()
        setInterval(updateDeveloperDashboardData, 5000)
    }
})

const updateHtmlValues = (jobsWaiting, jobsDone) => {
    if (jobsWaiting === null || jobsDone === null) {
        // Handle the case where value or total is null,
        // indicating Job Queue Error from dashboard
        document.getElementById(id+'-number').textContent = "Error";
    }
    else {
        let ids = ['jobs-waiting', 'jobs-done']
        let numerators = [jobsWaiting, jobsDone]
        let totalJobs = jobsWaiting + jobsDone

        for (let [i, id] of ids.entries()) {
            let percent = (numerators[i]/totalJobs) * 100;
            document.getElementById(id+'-number').textContent = numerators[i].toLocaleString('en');
            document.getElementById(id+'-circle-percentage').textContent = `${percent.toFixed(1)}%`;
            document.getElementById(id+'-circle-front').style.strokeDasharray = `${percent}, 100`;
        }
    }
}

/**
 * Calculates the progression towards corpus
 * @param jobTypeCountsDone : array of number of jobs for each job type (dockets, documents, comments, attachments) completed
 * @param totalJobs : array of number of jobs from Regulations for each job type 
 * TODO: totalJobs should ideally be be an int that is calculated
 */
const updateCorpusProgressHtml = (jobTypeCountsDone, totalJobs) => {
    let totalCorpus = 0
    let currentProgress = 0
    for (let i = 0; i < jobTypeCountsDone.length; i++) {
        currentProgress += jobTypeCountsDone[i]
        totalCorpus += totalJobs[i]
    }
    let percent = (currentProgress/totalCorpus) * 100;
    document.getElementById('progress-to-corpus-bar-percentage').textContent = `${percent.toFixed(2)}%`
    const progressBar = document.querySelector('.progress-bar-to-corpus');

    // Set the width of the progress bar to the calculated percentage
    progressBar.style.width = `${percent}%`;
}


const updateStatus = (container, status) => {
        let status_span = document.getElementById(container)
        if (status == "running") {
            status_span.textContent = "RUNNING";
            status_span.style.color = "green"
        }
        else {
            status_span.textContent = 'ERROR';
            status_span.style.color = "red"
        }

}

const updateCount = (id, value) => {
    document.getElementById(id+'-number').textContent = value.toLocaleString('en');
}

const updateJobTypeProgress = (id, value, total) => {
    let percent = (value/total) * 100;
    document.getElementById(id+'-percent').textContent = `${percent.toFixed(2)}%`;
}

const updateJobsQueuedByType = (id, value) => {
    document.getElementById(id+'-number').textContent = value;
}

const updateClientDashboardData = () => {
    fetch(`${BASE_URL}data`)
    .then(response => response.json())
    .then(jobInformation => {
        const {
            jobs_total,
            num_attachments_done,
            num_comments_done,
            num_dockets_done,
            num_documents_done,
            num_jobs_done, 
            num_jobs_waiting,
            num_jobs_comments_queued,
            num_jobs_dockets_queued,
            num_jobs_documents_queued,
        } = jobInformation;
        updateHtmlValues(num_jobs_waiting, num_jobs_done);
        updateCorpusProgressHtml([num_dockets_done, num_documents_done, num_comments_done, num_attachments_done], [232255, 1718669, 18072106, 15000000]); //TO DO: change hard coded numbers
        // Counts for percents
        updateJobTypeProgress("dockets-done",num_dockets_done, 232255);
        // Current estimate of number of attachments (from comments)
        updateJobTypeProgress("attachments-done",num_attachments_done, 15000000); 
        updateJobTypeProgress("comments-done",num_comments_done, 18072106);
        updateJobTypeProgress("documents-done",num_documents_done, 1718669);
        // Counts for numbers
        updateCount("dockets-done",num_dockets_done);
        // Current estimate of number of attachments (from comments)
        updateCount("attachments-done",num_attachments_done); 
        updateCount("comments-done",num_comments_done);
        updateCount("documents-done",num_documents_done);
        updateJobsQueuedByType("comments-queued", num_jobs_comments_queued);
        updateJobsQueuedByType("dockets-queued", num_jobs_dockets_queued);
        updateJobsQueuedByType("documents-queued", num_jobs_documents_queued);
        
    })
    .catch((err) => console.log(err));
}

const updateDeveloperDashboardData = () => {
    fetch(`${BASE_URL}data`)
    .then(response => response.json())
    .then(jobInformation => {

        const {
            client1,
            client2,
            client3,
            client4,
            client5,
            client6,
            client7,
            client8,
            client9,
            client10,
            client11,
            client12,
            client13,
            client14,
            client15,
            client16,
            client17,
            client18,
            client19,
            client20,
            client21,
            client22,
            client23,
            client24,
            client25,
            nginx,
            mongo,
            redis,
            work_generator,
            work_server, 
            rabbitmq
        } = jobInformation;

        updateStatus('client1-status', client1)
        updateStatus('client2-status', client2)
        updateStatus('client3-status', client3)
        updateStatus('client4-status', client4)
        updateStatus('client5-status', client5)
        updateStatus('client6-status', client6)
        updateStatus('client7-status', client7)
        updateStatus('client8-status', client8)
        updateStatus('client9-status', client9)
        updateStatus('client10-status', client10)
        updateStatus('client11-status', client11)
        updateStatus('client12-status', client12)
        updateStatus('client13-status', client13)
        updateStatus('client14-status', client14)
        updateStatus('client15-status', client15)
        updateStatus('client16-status', client16)
        updateStatus('client17-status', client17)
        updateStatus('client18-status', client18)
        updateStatus('client19-status', client19)
        updateStatus('client20-status', client20)
        updateStatus('client21-status', client21)
        updateStatus('client22-status', client22)
        updateStatus('client23-status', client23)
        updateStatus('client24-status', client24)
        updateStatus('client25-status', client25)
        updateStatus('nginx-status', nginx)
        updateStatus('mongo-status', mongo)
        updateStatus('redis-status', redis);
        updateStatus('work-generator-status', work_generator);
        updateStatus('work-server-status', work_server);
        updateStatus('rabbitmq-status', rabbitmq);
    })
    .catch((err) => console.log(err));
} 
