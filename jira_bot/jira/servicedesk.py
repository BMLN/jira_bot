import requests
from requests.auth import HTTPBasicAuth






def subdict(d: dict, keys):
    assert isinstance(d, dict)
    #assert all((x in d.keys() for x in keys)) 

    return { k: d.get(k, None) for k in keys }


def unnest_items(d, keys=None):
    assert keys == None or isinstance(keys, list)
    result = []
    
    def recurse(val, keys=None):
        if isinstance(val, dict):
            for k, v in val.items():
                if keys == None or k in keys:
                    recurse(v, keys)
                    
        elif isinstance(val, list):
            for item in val:
                recurse(item, keys)
        else:
            result.append(val)
    
    recurse(d, keys)

    
    return result






class Jira():
    
    def __init__(self, jira_url, auth=None):
        self.jira_url = jira_url
        if auth:
            self.auth(**auth)
        else:
            self.creds = auth

    
    #currently only basicauth
    def auth(self, **kwargs):
        assert "email" in kwargs and "api_token" in kwargs

        self.creds = HTTPBasicAuth(kwargs.get("email"), kwargs.get("api_token"))
        self.accountId = self.call("api/3/myself").get("accountId") #also involves auth check


    def call(self, resource, type="GET", params=None, payload=None):
        url =  f"{self.jira_url}/rest/{resource}"   
        headers = { "Accept": "application/json", "Content-Type": "application/json" }

        match type:
            case "GET":
                httpcall = requests.get
            case "POST":
                httpcall = requests.post
            case "PUT":
                httpcall = requests.put
            case "DELETE":
                httpcall = requests.delete
            case _:
                raise ValueError("Expected [GET, POST, PUT, DELETE]")


        if (response := httpcall(url, headers=headers, params=params, json=payload, auth=self.creds)).ok:
            return response.json()
            
        else:
            raise Exception(response.status_code)
            

    def fetchServicedesks(self):
        projects = self.call("/rest/servicedeskapi/servicedesk").get("values", [])

        return [ {"id": x.get("id", None), "projectKey": x.get("projectKey", None), "projectName": x.get("projectName", None)} for x in projects if "servicedesk" in x.get("_links", {}).get("self", "") ]

    

class JiraServicedesk():

    def __init__(self, jira, name):
        self.jira = jira
        self.project = next(filter(lambda x: name.lower() in x.get("projectName", "").lower(), self.jira.fetchServicedesks()), None)
        assert self.project
        self.fields = ["creator", "assignee", "updated", "description", "summary"] #"assignee,status,issuekey,updated,description,summary,comment"


    def fetchTickets(self, limit=50):
        tickets = self.jira.call(
            f"rest/api/3/search", 
            params={
                "jql": f"project={self.project.get("projectKey")} AND statusCategory != Done", 
                "fields": f'"{str.join(", ", self.fields)}"'  
            } | ({"maxResults": limit} if limit else {})
        ).get("issues", [])
        tickets = [ subdict(x, ["id", "key"]) | subdict(x.get("fields", {}), self.fields) for x in tickets ]
   
        return tickets
    

    def fetchTicket(self, ticketid):
        ticket = self.jira.call(f"rest/api/3/issue/{ticketid}", params={"fields": f'{str.join(", ", self.fields + ["comment"])}'})
        ticket = subdict(ticket, ["id", "key"]) | subdict(ticket.get("fields"), self.fields) | {"messages": ticket.get("fields", {}).get("comment", {}).get("comments", [])}
        ticket["creator"] = (ticket["creator"] or {}).get("accountId", None)
        ticket["assignee"] = (ticket["assignee"] or {}).get("accountId", None)
        ticket["messages"] = [ {
            "id": x.get("id", None),
            "author": x.get("author", {}).get("accountId", None),
            "text": str.join("", unnest_items(x.get("body", {}), ["text"]))
        } for x in ticket["messages"] ]

        #TODO: super ugly sofar
        initial_title = ticket["summary"] if ticket["summary"] else ""
        initial_desc = str.join("",[ x for x in unnest_items(ticket["description"], ["text"]) if x ])
        initial = ""

        if initial_title:
            initial += initial_title
        if initial_desc:
            if initial:
                initial += ": "
            initial += initial_desc
        if initial:
            ticket["messages"].insert(0, {"id": None, "author": ticket.get("creator"), "text": initial})


        return ticket
    
    
    def postMessageTo(self, ticketid, message, public=True):
        self.jira.call(
            f"rest/servicedeskapi/request/{ticketid}/comment", 
            "POST", 
            payload={"body": message, "public": public}
        )
