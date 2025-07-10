import sys
import os
from psutil import virtual_memory
from data.load import from_file, estimate_chunks


from chatbot.src.instances.knowledgebases import WeaviateKB

import pandas as pd
from ast import literal_eval







from logging import getLogger
logger = getLogger()










def preproc(x):
    if x is None:
        return None
    
    if isinstance(x, str):
        return literal_eval(x)
    
    return x








#init

#configuration
h = os.environ.get("CHATBOT_KB_HOST", None)
p = os.environ.get("CHATBOT_KB_PORT", None)
c = os.environ.get("CHATBOT_KB_COLLECTION", None)

error_threshold = float(os.environ.get("CHATBOT_KB_ERRORTHRESHOLD", 0.80))







if __name__ == "__main__":
    
    if not all([h, p, c]):
        logger.error(f"didn't provide all connection variables")
        sys.exit(1) 



    #connection
    try:
        conn = WeaviateKB(h, p, c)
    except:
        logger.error(f"couldn't connect to knowledgebase[{WeaviateKB.__name__}]")
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

                chunk = chunk[chunk.columns.intersection(["id", "data", "embedding"])]
                chunk["id"] = chunk["id"].apply(preproc) if "id" in chunk else None
                chunk["data"] = chunk["data"].apply(preproc)
                chunk["embedding"] = chunk["embedding"].apply(preproc)
                
                
                conn.create(
                    id=chunk["id"],
                    embedding=chunk["embedding"],
                    data=chunk["data"]
                )
                del chunk

            succesful_reads.append(True)


        except Exception as e:
            logger.error(f"could't read {arg}: {str(e)}")
            succesful_reads.append(False)


    if succesful_reads and sum(succesful_reads) / len(succesful_reads) < error_threshold:
        logger.error(f"too many reads failed! ({sum(succesful_reads)}/{len(succesful_reads)})")
        sys.exit(1)
