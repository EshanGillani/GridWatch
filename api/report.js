const OWNER = "EshanGillani";
const REPO = "GridWatch";
const PATH = "reports.json";

export default async function handler(req,res){

if(req.method !== "POST"){
return res.status(405).json({error:"Method not allowed"});
}

const {location,type,description} = req.body;

if(!location || !type){
return res.status(400).json({error:"Missing data"});
}

const token = process.env.GH_TOKEN;

const headers = {
Authorization:`Bearer ${token}`,
Accept:"application/vnd.github.v3+json"
};

const file = await fetch(
`https://api.github.com/repos/${OWNER}/${REPO}/contents/${PATH}`,
{headers}
);

const data = await file.json();

const json = JSON.parse(Buffer.from(data.content,"base64").toString());

json.reports.push({
location,
type,
description,
reportedAt:new Date().toISOString()
});

await fetch(
`https://api.github.com/repos/${OWNER}/${REPO}/contents/${PATH}`,
{
method:"PUT",
headers:{
...headers,
"Content-Type":"application/json"
},
body:JSON.stringify({
message:`report: ${type} in ${location}`,
content:Buffer.from(JSON.stringify(json,null,2)).toString("base64"),
sha:data.sha
})
});

res.status(200).json({message:"Report submitted successfully"});
}