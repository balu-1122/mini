// scripts.js

document.addEventListener("DOMContentLoaded", function() {
    const applyButtons = document.querySelectorAll('.apply-form');
    const modal = document.getElementById('jobModal');
    const closeBtn = document.querySelector('.close-btn');

    // Dynamic effect to open job details in modal
    applyButtons.forEach(button => {
        button.addEventListener('submit', function(e) {
            e.preventDefault();

            // Get job details dynamically
            const jobRow = button.closest('.job-row');
            const jobTitle = jobRow.querySelector('.job-title').innerText;
            const jobDescription = jobRow.querySelector('.job-description').innerText;
            const jobLocation = jobRow.querySelector('.job-location').innerText;
            const jobSalary = jobRow.querySelector('.job-salary').innerText;
            const jobCompany = jobRow.querySelector('.job-company').innerText;

            // Update modal content
            document.getElementById('modalJobTitle').innerText = jobTitle;
            document.getElementById('modalJobDescription').innerText = jobDescription;
            document.getElementById('modalJobLocation').innerText = jobLocation;
            document.getElementById('modalJobSalary').innerText = jobSalary;
            document.getElementById('modalJobCompany').innerText = jobCompany;

            // Display modal
            modal.style.display = "block";
        });
    });

    // Close modal when clicking on the close button
    closeBtn.addEventListener('click', function() {
        modal.style.display = "none";
    });

    // Close modal when clicking outside the modal content
    window.addEventListener('click', function(e) {
        if (e.target == modal) {
            modal.style.display = "none";
        }
    });
});
