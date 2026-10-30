function filterComplaints(status, selectedTab) {

    // Get all complaint cards
    const cards = document.querySelectorAll(".complaint-card");

    // Get all tabs
    const tabs = document.querySelectorAll(".tab");


    // Remove active from all tabs
    tabs.forEach(function(tab) {
        tab.classList.remove("active");
    });


    // Make clicked tab active
    selectedTab.classList.add("active");


    // Show / hide complaints
    cards.forEach(function(card) {

        const complaintStatus =
            card.getAttribute("data-status");


        if (status === "All") {

            card.style.display = "flex";

        }
        else if (complaintStatus === status) {

            card.style.display = "flex";

        }
        else {

            card.style.display = "none";

        }

    });
}


/* Open Complaint Details */

function openDetails(complaintId) {

    window.location.href =
        "complaint-details.html?id=" +
        encodeURIComponent(complaintId);

}


/* Back to Dashboard */

function goBack() {

    window.location.href = "dashboard.html";

}