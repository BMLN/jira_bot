from jira.servicedesk import JiraServicedesk
from chatbot.src.interfaces.chatbot import Chatbot


import datetime

from time import sleep
from queue import Queue
from threading import Thread



from logging import getLogger

logger = getLogger()





class Controller():

    def __init__(self, servicedesk: JiraServicedesk, chatbot: Chatbot, update_freq=60):
        self.servicedesk = servicedesk
        self.chatbot = chatbot
        self.ticket_queue = Queue()
        self.update_freq=60
        self.updated = datetime.datetime.now() - datetime.timedelta(days=30)
        logger.info(f"setup jira_bot on {servicedesk.project.get("projectName", None)}({servicedesk.jira.jira_url})")

        self.worker = None


    def update(self):
        updated = datetime.datetime.now()

        changedTickets = self.servicedesk.fetchTickets()
        changedTickets = [ x for x in changedTickets if (datetime.datetime.fromisoformat(x.get("updated", None)).timestamp() or datetime.datetime.now().timestamp()) > self.updated.timestamp() ]

        
        for x in changedTickets: 
            self.ticket_queue.put(x)
            #self.processTicket(x["key"])
            
        self.updated = updated

        logger.info(f"jira_bot updated at {str(self.updated.strftime("%Y-%m-%d %H:%M"))}")



    def processTicket(self, ticketid):
        ticket = self.servicedesk.fetchTicket(ticketid)

        if (messages := ticket.get("messages")):   #should always be true however
            if messages[-1]["author"] == ticket["creator"] and messages[-1]["author"] != self.servicedesk.jira.accountId:
                logger.info(f"jira_bot is processing ticket {ticketid}")

                #create response
                inquiry = messages[-1]["text"] #last message only? Need testing for best contextwindow
                response = self.chatbot.respond(inquiry) #"here it would invoke a chatrequest" 

                #post response
                self.servicedesk.postMessageTo(ticket["id"], "---!AUTOMATED MESSAGE! CURRENTLY IN TESTING! ONLY CONTAINS END-TO-END COURSE DATA!---\n" + response, False) #for current testing stage
                    
                logger.info(f"jira_bot posted a message to {ticketid}")






    def start(self):
        logger.info(f"starting jira_bot on {self.servicedesk.project.get("projectName", None)}({self.servicedesk.jira.jira_url})")

        def worker_start():
                while True:
                    ticket = self.ticket_queue.get()
                    
                    try:
                        self.processTicket(ticket["id"])
                        
                    except Exception as e:
                        logger.error(e)
                        
                    finally:
                        self.ticket_queue.task_done()


        Thread(
            target=worker_start, 
            daemon=True
        ).start()

        while True:
            try:
                self.update()
            except Exception as e:
                logger.warning(f"jira_bot failed to update at { str(datetime.now().strftime("%Y-%m-%d %H:%M")) }")

            sleep(self.update_freq)
