export default function handler(req,res){

global.reports = global.reports || []

res.json({
reports: global.reports
})
}