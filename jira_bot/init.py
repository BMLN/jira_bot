import sys
import os
from psutil import virtual_memory
from data.load import from_file, estimate_chunks


from chatbot.src.instances.knowledgebases import WeaviateKB

import pandas as pd
from ast import literal_eval







from logging import getLogger
logger = getLogger()








#init

#configuration
h = os.environ.get("CHATBOT_KB_HOST", None)
p = os.environ.get("CHATBOT_KB_PORT", None)
c = os.environ.get("CHATBOT_KB_COLLECTION", None)

error_threshold = float(os.environ.get("CHATBOT_KB_ERRORTHRESHOLD", 0.80))


if not all([h, p, c]):
    logger.warning(f"didn't provide all connection variables")
    sys.exit(1) 



#connection
try:
    conn = WeaviateKB(h, p, c)
except:
    logger.warning(f"couldn't connect to knowledgebase[{WeaviateKB.__name__}]")
    sys.exit(1)



#read/write
succesful_reads = []

for arg in sys.argv[1:]:
    try:
        logger.info(f"initializing from {arg}...")
        
        chunking = estimate_chunks(arg, virtual_memory().available, load=0.5)
        data = from_file(arg, arg.split(".")[-1], encoding="utf-8", chunk_size=chunking)
        if isinstance(data, pd.DataFrame): data=[data]

        
        for chunk in data:
            if not ("embedding" in chunk and "data" in chunk):
                logger.warning(f"missing [{ str.join(", ", [_x for _x in ["embedding", "data"] if _x not in chunk])}] in {arg}")
                break

            conn.create(
                id=chunk["id"] if "id" in chunk else None,
                embedding=chunk["embedding"].apply(literal_eval),
                data=chunk["data"].apply(literal_eval)
            )
            del chunk
        succesful_reads.append(True)


    except Exception as e:
        logger.warning(f"could't read {arg}")
        succesful_reads.append(False)



if sum(succesful_reads) / len(succesful_reads) < error_threshold:
    logger.warning(f"too many reads failed! ({sum(succesful_reads)}/{len(succesful_reads)})")
    sys.exit(1)