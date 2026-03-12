export default async function hander(req,res){
    if(req.method !== "POST"){
        return res.status(405).json({error:"Method not allowed"})
    }


const { zip, type, description } = req.body

const report={
    zip,
    type,
    description,
    time:Date.now()
}

global.reports = global.reports || []

global.reports.push(report)

res.json({message:"Report submitted"})
}