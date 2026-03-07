const map = L.map('map').setView([38.9,-77.03],8);

L.tileLayer(
'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
{ attribution:'OSM'}
).addTo(map);

let clusterGroup = L.markerClusterGroup();
let heatPoints = [];
let heatLayer = L.heatLayer([], {radius:25});

map.addLayer(clusterGroup);
map.addLayer(heatLayer);

async function loadOutages(){

clusterGroup.clearLayers();
heatPoints = [];

const res = await fetch("data/outages.geojson");
const data = await res.json();

let countyTotals = {};

data.features.forEach(feature=>{

const coords = feature.geometry.coordinates;
const props = feature.properties;

const lat = coords[1];
const lon = coords[0];

let severityColor = "green";

if(props.customers > 1000) severityColor = "red";
else if(props.customers > 200) severityColor = "orange";

const marker = L.circleMarker([lat,lon],{
radius:8,
color:severityColor
});

marker.bindPopup(
`<b>${props.county}</b><br>
Customers Out: ${props.customers}`
);

clusterGroup.addLayer(marker);

heatPoints.push([lat,lon,props.customers/1000]);

if(!countyTotals[props.county])
countyTotals[props.county] = 0;

countyTotals[props.county] += props.customers;

});

heatLayer.setLatLngs(heatPoints);

renderSidebar(countyTotals);

}

function renderSidebar(totals){

let html = "";

Object.keys(totals).forEach(c=>{

html += `<div class="county">
${c}: ${totals[c]} customers
</div>`;

});

document.getElementById("stats").innerHTML = html;

}

loadOutages();

setInterval(loadOutages,300000);