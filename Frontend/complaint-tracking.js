const params =
    new URLSearchParams(window.location.search);

const complaintId =
    params.get("id");


if (complaintId) {

    document.getElementById("complaintId")
        .textContent = complaintId;

}


/* Back to Complaint Details */

function goBack() {

    const id =
        document.getElementById("complaintId")
        .textContent;

    window.location.href =
        "complaint-details.html?id=" +
        encodeURIComponent(id);
}


/* Go to Dashboard */

function goHome() {

    window.location.href = "dashboard.html";

}