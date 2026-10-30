// ======================================
// COMPLAINT DATA
// ======================================

const complaints = {

    "GC2024 0515 0001": {

        category: "Roads",

        status: "Pending",

        date: "15 May 2024",

        description:
            "There is a big pothole on the main road near the temple.",

        photo:
            "images/pothole.jpg",

        submitted:
            "15 May 2024, 10:00 AM",

        progress:
            "Pending"

    },


    "GC2024 0510 0002": {

        category: "Water Supply",

        status: "In Progress",

        date: "10 May 2024",

        description:
            "Water supply has been interrupted in our village area.",

        photo:
            "images/water.jpg",

        submitted:
            "10 May 2024, 09:30 AM",

        progress:
            "12 May 2024, 04:15 PM"

    },


    "GC2024 0506 0003": {

        category: "Street Lights",

        status: "Resolved",

        date: "06 May 2024",

        description:
            "Street lights are not working near the village road.",

        photo:
            "images/streetlight.jpg",

        submitted:
            "06 May 2024, 10:00 AM",

        progress:
            "07 May 2024, 03:30 PM"

    },


    "GC2024 0504 0004": {

        category: "Garbage",

        status: "Pending",

        date: "04 May 2024",

        description:
            "Garbage has not been collected from our street.",

        photo:
            "images/garbage.jpg",

        submitted:
            "04 May 2024, 11:00 AM",

        progress:
            "Pending"

    }

};


// ======================================
// GET ID FROM URL
// ======================================

const params =
    new URLSearchParams(window.location.search);

const id =
    params.get("id");


// ======================================
// FIND COMPLAINT
// ======================================

const complaint =
    complaints[id];


// ======================================
// DISPLAY DETAILS
// ======================================

if (complaint) {

    document.getElementById("complaintId")
        .textContent = id;

    document.getElementById("category")
        .textContent = complaint.category;

    document.getElementById("status")
        .textContent = complaint.status;

    document.getElementById("date")
        .textContent = complaint.date;

    document.getElementById("description")
        .textContent = complaint.description;

    document.getElementById("complaintPhoto")
        .src = complaint.photo;

    document.getElementById("submittedDate")
        .textContent = complaint.submitted;

    document.getElementById("progressDate")
        .textContent = complaint.progress;

}


// ======================================
// BACK BUTTON
// ======================================

function goBack() {

    window.location.href =
        "my-complaints.html";

}


// ======================================
// TRACK COMPLAINT
// ======================================

function trackComplaint() {

    window.location.href =
        "complaint-tracking.html?id=" +
        encodeURIComponent(id);

}