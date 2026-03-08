// create map
const map = L.map("map").setView([37.5, -78.5], 7);

// add map tiles
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap"
}).addTo(map);

// store markers
let markers = [];

// sample outage data (temporary)
const outageData = [
  { provider: "Dominion Energy", lat: 37.54, lng: -77.43, customers: 1200 },
  { provider: "Dominion Energy", lat: 38.03, lng: -78.48, customers: 450 },
  { provider: "Appalachian Power", lat: 37.27, lng: -79.94, customers: 800 },
  { provider: "NOVEC", lat: 38.75, lng: -77.47, customers: 320 },
  { provider: "Dominion Energy", lat: 36.85, lng: -76.29, customers: 1500 }
];

// load outages
function loadOutages() {

  // remove old markers
  markers.forEach(m => map.removeLayer(m));
  markers = [];

  outageData.forEach(o => {

    const marker = L.circleMarker([o.lat, o.lng], {
      radius: Math.sqrt(o.customers) / 2,
      color: "red"
    })
    .bindPopup(`${o.provider}<br>${o.customers} customers out`)
    .addTo(map);

    markers.push(marker);

  });

}

// first load
loadOutages();

// update every minute (still works if data changes later)
setInterval(loadOutages, 60000);