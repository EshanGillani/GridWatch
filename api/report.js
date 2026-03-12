export default async function handler(req,res){

if(req.method !== "POST"){
return res.status(405).json({error:"Method not allowed"})
}

const { zip, type, description } = req.body

const geo = await fetch(`https://api.zippopotam.us/us/${zip}`)
const geoData = await geo.json()

const lat = parseFloat(geoData.places[0].latitude)
const lng = parseFloat(geoData.places[0].longitude)

const report={
zip,
type,
description,
lat,
lng,
time:Date.now()
}

global.reports = global.reports || []
global.reports.push(report)

res.json({message:"Report submitted"})
}