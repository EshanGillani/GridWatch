import fs from "fs"

export default function handler(req,res){

let reports=[]

if(fs.existsSync("reports.json")){
reports=JSON.parse(fs.readFileSync("reports.json"))
}

res.json({reports})
}