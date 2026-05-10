'use strict';

const BASE_URL = window.location.href;
const RADIUS = 80;
const NUMBER_ANIMATION_STEP = 4;
let unknown = false;

window.addEventListener('load', function init() {
    if (window.location.pathname === '/') {
        updateClientDashboardData();
        setInterval(updateClientDashboardData, 500);
    } else if (window.location.pathname === '/dev') {
        updateDeveloperDashboardData();
        setInterval(updateDeveloperDashboardData, 500);
    }
})

/**
 * Calculates the progression towards corpus
 * @param jobTypeCountsDone : array of number of jobs for each job type (dockets, documents, comments, attachments) completed
 * @param totalCorpus : amount of jobs available from Regulations (dockets, documents, comments)
 * @param mirrulationsBucketSize : the size of the mirrulations bucket on S3
 */
const updateCorpusProgressHtml = (jobTypeCountsDone, totalCorpus, mirrulationsBucketSize) => {
    let currentProgress = 0;
    for (let i = 0; i < jobTypeCountsDone.length; i++) {
        currentProgress += jobTypeCountsDone[i];
    }
    const percent = totalCorpus > 0 ? (currentProgress / totalCorpus) * 100 : 0;
    if (!unknown) {
        document.getElementById('progress-to-corpus-bar-percentage').textContent = `${percent.toFixed(2)}%`;
        document.getElementById('total-size').textContent = mirrulationsBucketSize
    } else {
        document.getElementById('progress-to-corpus-bar-percentage').textContent = `Unknown`
    }
    const progressBar = document.querySelector('.progress-bar-to-corpus');

    // Set the width of the progress bar to the calculated percentage
    progressBar.style.width = `${percent}%`;
}

const updateHtmlValues = (jobsWaiting, jobsDone) => {
    if (jobsWaiting === null || jobsDone === null) {
        // Handle the case where value or total is null,
        // indicating Job Queue Error from dashboard
        unknown = true;
        document.getElementById('jobs-waiting-number').textContent = "Unknown";
        document.getElementById('jobs-done-number').textContent = "Unknown";
    }
    else {
        let ids = ['jobs-waiting', 'jobs-done'];
        let numerators = [jobsWaiting, jobsDone];
        let totalJobs = jobsWaiting + jobsDone;

        for (let [i, id] of ids.entries()) {
            let percent = totalJobs > 0 ? (numerators[i] / totalJobs) * 100 : 0;
            document.getElementById(id+'-number').textContent = numerators[i].toLocaleString('en');
            document.getElementById(id+'-circle-percentage').textContent = `${percent.toFixed(1)}%`;
            document.getElementById(id+'-circle-front').style.strokeDasharray = `${percent}, 100`;
        }
    }
}

const updateStatus = (container, state) => {
        let status_span = document.getElementById(container)
        let text = "NOT RUNNING";
        let color = "grey";


        if (state) {
        switch(state.status) {
            case "running":
                text = "RUNNING";
                color = "green";
                break;
            case "exited":
                text = "EXITED";
                color = "red";
                break;
            default:
                text = state.status.toUpperCase();
                color = "orange";
        }}

        status_span.textContent = text;
        status_span.style.color = color;
}

const updateJobTypeProgress = (id, value, total) => {
    if (!unknown) {
        const percent = total > 0 ? (value / total) * 100 : 0;
        document.getElementById(id+'-percent').textContent = `${percent.toFixed(2)}%`;
    } else {
        document.getElementById(id+'-percent').textContent = "Unknown";
    }
}

const updateCount = (id, value) => {
    if (!unknown) {
        document.getElementById(id+'-number').textContent = Math.ceil(value).toLocaleString('en');
    } else {
        document.getElementById(id+'-number').textContent = " "
    }
}

const updateClientDashboardData = () => {
    fetch(`${BASE_URL}data`)
    .then(response => response.json())
    .then(jobInformation => {
        const {
            num_attachments_done,
            num_comments_done,
            num_dockets_done,
            num_documents_done,
            num_jobs_done, 
            num_jobs_waiting,
            regulations_total_dockets,
            regulations_total_documents,
            regulations_total_comments,
            mirrulations_bucket_size
        } = jobInformation;

        const regulations_total_attachments = num_comments_done > 0
            ? (num_attachments_done / num_comments_done) * regulations_total_comments
            : 0;
        const regulations_totals = regulations_total_dockets + regulations_total_documents + regulations_total_comments + regulations_total_attachments;

        updateHtmlValues(num_jobs_waiting, num_jobs_done);
        updateCorpusProgressHtml([num_dockets_done, num_documents_done, num_comments_done, num_attachments_done], regulations_totals, mirrulations_bucket_size);
        // Counts for percents
        updateJobTypeProgress("dockets-done", num_dockets_done, regulations_total_dockets);
        updateJobTypeProgress("documents-done",num_documents_done, regulations_total_documents);
        updateJobTypeProgress("comments-done",num_comments_done, regulations_total_comments);
        // Current estimate of number of attachments (from comments)
        updateJobTypeProgress("attachments-done",num_attachments_done, regulations_total_attachments); 
        // Counts for numbers
        updateCount("dockets-done",num_dockets_done);
        updateCount("documents-done",num_documents_done);
        updateCount("comments-done",num_comments_done);
        updateCount("attachments-done",num_attachments_done);
        updateCount("regulations-total-dockets", regulations_total_dockets);
        updateCount("regulations-total-documents", regulations_total_documents);
        updateCount("regulations-total-comments", regulations_total_comments);
        updateCount("regulations-total-attachments", regulations_total_attachments);
        
    })
    .catch((err) => console.log(err));
}

const updateDeveloperDashboardData = () => {
    fetch(`${window.location.origin}/devdata`)
    .then(response => response.json())
    .then(jobInformation => {

        const {
            client,
            nginx,
            redis,
            work_generator,
            rabbitmq
        } = jobInformation;

        updateStatus('client-status', client);
        updateStatus('nginx-status', nginx);
        updateStatus('redis-status', redis);
        updateStatus('work-generator-status', work_generator);
        updateStatus('rabbitmq-status', rabbitmq);
    })
    .catch((err) => console.log(err));
} 
