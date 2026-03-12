import fs from "fs"
import os from "os"
import path from "path"

const REPORTS_FILE = path.join(os.tmpdir(), "gridwatch-reports.json")

export default function handler(req,res){

let reports=[]
if(fs.existsSync(REPORTS_FILE)){
reports=JSON.parse(fs.readFileSync(REPORTS_FILE))
}

res.json({reports})
}
