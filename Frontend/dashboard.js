// ===============================
// GRAMSATHI DASHBOARD
// ===============================

// Search Services
const searchInput = document.querySelector(".search-box input");
const serviceCards = document.querySelectorAll(".service-card");

if (searchInput) {
    searchInput.addEventListener("input", function () {

        const searchText = this.value.toLowerCase().trim();

        serviceCards.forEach(function (card) {

            const serviceName = card.innerText.toLowerCase();

            if (serviceName.includes(searchText)) {
                card.style.display = "flex";
            } else {
                card.style.display = "none";
            }

        });
    });
}


// Explore Services button
const exploreButton = document.querySelector(".explore-btn");

if (exploreButton) {
    exploreButton.addEventListener("click", function () {

        const servicesSection = document.querySelector(".services");

        if (servicesSection) {
            servicesSection.scrollIntoView({
                behavior: "smooth"
            });
        }

    });
}


// ===============================
// TOTAL COMPLAINTS COUNT
// ===============================

const totalComplaintsCount =
    document.getElementById("totalComplaintsCount");

if (totalComplaintsCount) {
    const totalComplaints =
        localStorage.getItem("totalComplaints") || 12;

    totalComplaintsCount.textContent = totalComplaints;
}