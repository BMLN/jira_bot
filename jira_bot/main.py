from os import environ
from time import sleep


from jira_bot.jira_NEW.servicedesk import Jira, JiraServicedesk
from controller import Controller
from chatbot import src





from logging import getLogger, basicConfig, INFO

logger = getLogger()




if __name__ == "__main__":
    basicConfig(level=INFO)


    
    jira = Jira(environ["JIRA_URL"], {"email": environ["JIRA_AUTH_EMAIL"], "api_token": environ["JIRA_AUTH_TOKEN"]})
    serviceDesk = JiraServicedesk(jira, environ["JIRA_SERVICEDESK"])

    chatbot = None
    #adddata


    controller = Controller(chatbot, serviceDesk)
    freq = int(environ["BOT_UPDATE_FREQUENCY"])

    while True:
        try:
            controller.update()
            
        except Exception as e:
            logger.error(e)

        sleep(freq)




#### new 
#no class 

from jira_bot.chatbot.cp.interfaces.chatbot import Chatbot

from jira_bot.chatbot.cp.instances.knowledgebases import WeaviateKB
from jira_bot.chatbot.cp.instances.vectorizers import OnDemandDPREncoder
#from jira_bot.chatbot.cp.instances.match
from jira_bot.chatbot.cp.instances.instructors import OllamaInstructor
from jira_bot.chatbot.cp.instances.generators import OnDemandGenerator





if __name__ == "__main__":
    basicConfig(level=INFO)

    jira_url = environ.get("JIRA_URL", None)
    jira_auth_email = environ.get("JIRA_AUTH_EMAIL", None)
    jira_auth_token = environ.get("JIRA_AUTH_TOKEN", None)
    
    jira_servicedesk = environ.get("JIRA_SERVICEDESK", None)

    


    #jira
    jira = Jira(jira_url, {"email": jira_auth_email, "api_token": jira_auth_token})
    servicedesk = JiraServicedesk(jira, jira_servicedesk)
    
    #chatbot
    knowledgebase = None
    vectorizer = OnDemandDPREncoder("")
    matcher = None
    instructor = None
    generator = None

    chatbot = Chatbot(
        knowledgebase,
        vectorizer,
        matcher,
        instructor,
        generator
    )

    Controller(chatbot, servicedesk).start()
    


    controller = Controller(chatbot, serviceDesk)
    freq = int(environ["BOT_UPDATE_FREQUENCY"])

    while True:
        try:
            controller.update()
            
        except Exception as e:
            logger.error(e)

        sleep(freq)
    




class JiraBot(Chatbot):

    def __init__(self, weavite_cfg, dpr_model_name, generator_model_name):
        assert "host" in weavite_cfg and "port" in weavite_cfg and "collection" in weavite_cfg

        
        kb = WeaviateKB(**weavite_cfg)
        vt = OnDemandDPREncoder(dpr_model_name)
        
        it = OllamaInstructor() #TODO: wrong one here
        gt = OnDemandGenerator(generator_model_name)

        super().__init__(kb, vt, matcher, it, gt)



