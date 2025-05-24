from jira_bot.chatbot.cp.interfaces.chatbot import Chatbot

from jira_bot.chatbot.cp.instances.knowledgebases import WeaviateKB
from jira_bot.chatbot.cp.instances.vectorizers import OnDemandDPREncoder
#from jira_bot.chatbot.cp.instances.match
from jira_bot.chatbot.cp.instances.instructors import OllamaInstructor
from jira_bot.chatbot.cp.instances.generators import OnDemandGenerator




class JiraBot(Chatbot):

    def __init__(self, weavite_cfg, dpr_model_name, generator_model_name):
        assert "host" in weavite_cfg and "port" in weavite_cfg and "collection" in weavite_cfg

        
        kb = WeaviateKB(**weavite_cfg)
        vt = OnDemandDPREncoder(dpr_model_name)
        
        it = OllamaInstructor() #TODO: wrong one here
        gt = OnDemandGenerator(generator_model_name)

        super().__init__(kb, vt, matcher, it, gt)



