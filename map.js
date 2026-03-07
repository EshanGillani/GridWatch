// create map
const map = L.map("map").setView([37.5, -78.5], 7);

// add map tiles
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap"
}).addTo(map);

// store markers
let markers = [];

// load outages
function loadOutages() {

  fetch("http://localhost:3000/api/outages")
    .then(res => res.json())
    .then(data => {

      // remove old markers
      markers.forEach(m => map.removeLayer(m));
      markers = [];

      data.forEach(o => {

        const marker = L.circleMarker([o.lat, o.lng], {
          radius: Math.sqrt(o.customers) / 2,
          color: "red"
        })
        .bindPopup(`${o.provider}<br>${o.customers} customers out`)
        .addTo(map);

        markers.push(marker);

      });

    });

}

// first load
loadOutages();

// update every minute
setInterval(loadOutages, 60000);