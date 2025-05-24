from jira_bot.jira_NEW.servicedesk import JiraServicedesk
from chatbot.src.interfaces.chatbot import Chatbot


import datetime







from logging import getLogger

logger = getLogger()





class Controller():

    def __init__(self, chatbot: Chatbot, servicedesk: JiraServicedesk):
        self.chatbot = chatbot
        self.servicedesk = servicedesk
        self.updated = datetime.datetime.now() - datetime.timedelta(days=30)
        logger.info(f"setup jira_bot on {servicedesk.project.get("projectName", None)}({servicedesk.jira.jira_url})")


    def update(self):
        updated = datetime.datetime.now()

        updatedTickets = self.servicedesk.fetchTickets()
        updatedTickets = [ x for x in updatedTickets if (datetime.datetime.fromisoformat(x.get("updated", None)).timestamp() or datetime.datetime.now().timestamp()) > self.updated.timestamp() ]
        
        
        for x in updatedTickets: self.processTicket(x["id"])
        self.updated = updated
        logger.info(f"jira_bot updated at {str(self.updated)}")


    def processTicket(self, ticketid):
        ticket = self.servicedesk.fetchTicket(ticketid)

        if (messages := ticket.get("messages")):   #should always be true however
            if messages[-1]["author"] == ticket["creator"] and messages[-1]["author"] != self.servicedesk.jira.accountId:
                
                #create response
                inquiry = messages[-1]["text"] #last message only? Need testing for best contextwindow
                response = "here it would invoke a chatrequest" #self.chatbot.repond(inquiry)

                #post response
                self.servicedesk.postMessageTo(ticket["id"], response, False) #for current testing stage
                logger.info("jira_bot posted a message to {ticketid}")
                print("don")