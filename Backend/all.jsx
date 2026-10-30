import React from "react";
import "./AllServices.css";

const services = [
  {
    name: "Raise Complaint",
    icon: "📝",
    color: "#f4b942",
  },
  {
    name: "Track Complaints",
    icon: "🔍",
    color: "#4caf9b",
  },
  {
    name: "My Complaints",
    icon: "♧",
    color: "#7b4bb7",
  },
  {
    name: "Announcements",
    icon: "◉",
    color: "#4caf8b",
  },
  {
    name: "Awareness",
    icon: "📢",
    color: "#408fc4",
  },
  {
    name: "Emergency Contacts",
    icon: "✚",
    color: "#e74c4c",
  },
  {
    name: "Weather & Crop Advisory",
    icon: "☀",
    color: "#4794c6",
  },
  {
    name: "Market Prices",
    icon: "🛒",
    color: "#f0a52b",
  },
  {
    name: "Panchayat Notices",
    icon: "♙",
    color: "#b56a91",
  },
  {
    name: "Feedback & Rating",
    icon: "♧",
    color: "#e8b62f",
  },
  {
    name: "Help & Support",
    icon: "?",
    color: "#8b57b5",
  },
  {
    name: "More Services",
    icon: "▦",
    color: "#344b91",
  },
];

function AllServices() {
  return (
    <div className="services-page">
      <div className="services-container">

        <h1>All Services</h1>

        <div className="services-grid">
          {services.map((service, index) => (
            <button
              className="service-card"
              key={index}
              onClick={() => console.log(service.name)}
            >
              <div
                className="service-icon"
                style={{ color: service.color }}
              >
                {service.icon}
              </div>

              <span>{service.name}</span>
            </button>
          ))}
        </div>

      </div>
    </div>
  );
}

export default AllServices;