import requests
import json
import time

def run_scraper():

    url="https://outagemap.dominionenergy.com/"

    r=requests.get(url)
    data=r.json()

    features=[]

    for outage in data["outages"]:
        features.append({
            "type":"Feature",
            "properties":{
                "county":outage["county"],
                "customers":outage["customers"]
            },
            "geometry":{
                "type":"Point",
                "coordinates":[outage["lon"],outage["lat"]]
            }
        })

    geojson={
        "type":"FeatureCollection",
        "features":features
    }

    with open("../data/outages.geojson","w") as f:
        json.dump(geojson,f)

while True:
    run_scraper()
    time.sleep(300)