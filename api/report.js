import fs from "fs"
import os from "os"
import path from "path"

const REPORTS_FILE = path.join(os.tmpdir(), "gridwatch-reports.json")

export const config = {
  api: {
    bodyParser: {
      sizeLimit: "4mb"
    }
  }
}

export default async function handler(req,res){

if(req.method !== "POST"){
return res.status(405).json({error:"Method not allowed"})
}

try{

const { zip, type, description, image } = req.body

let lat=null, lng=null
try{
const geo = await fetch(`https://api.zippopotam.us/us/${zip}`)
if(geo.ok){
const geoData = await geo.json()
lat = parseFloat(geoData.places[0].latitude)
lng = parseFloat(geoData.places[0].longitude)
}
}catch(geoErr){
console.error("Geo lookup failed:", geoErr)
}

const report={
zip,
type,
description,
image: image || null,
lat,
lng,
time:Date.now()
}

let reports=[]
if(fs.existsSync(REPORTS_FILE)){
reports=JSON.parse(fs.readFileSync(REPORTS_FILE))
}

reports.push(report)
fs.writeFileSync(REPORTS_FILE, JSON.stringify(reports))

res.json({message:"Report submitted"})

}catch(err){
console.error("Report handler error:", err)
res.status(500).json({error:"Failed to submit report: "+err.message})
}
}
