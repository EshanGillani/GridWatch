document.addEventListener("DOMContentLoaded", function () {

    const dropdown = document.getElementById("cityDropdown");

    dropdown.addEventListener("change", function () {
        updatePrediction();
    });

    // run once on page load
    updatePrediction();

});


function updatePrediction() {

    const city = document.getElementById("cityDropdown").value;

    const prediction = predictOutage(city);

    document.getElementById("prediction").innerText =
        "Predicted outages: " + prediction;

}


function predictOutage(city) {

    // Example prediction data
    const outageData = {
        "Fairfax": 120,
        "Arlington": 75,
        "Alexandria": 90,
        "Reston": 60
    };

    return outageData[city] || 0;

}