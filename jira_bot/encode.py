import sys
from os import path

from chatbot.src.instances.vectorizers import OnDemandDPREncoder
from data.load import estimate_chunks, from_file

from typing import Iterable
import pandas as pd


from argparse import ArgumentParser, ArgumentTypeError







def textsplit(data, batch_size=100):
    output = [[]]

    if not isinstance(data, str) and isinstance(data, Iterable):
        data = str.join(" ", data)

    if not isinstance(data, str):
        data = str(data)

        
    for x in data.split(" "):
        if len(output[-1]) > batch_size:
            output.append([])

        output[-1].append(x)
        
    output = [ str.join(" ", x) for x in output ]


    return output




def intornonetype(x):
    if x == None:
        return x
    if isinstance(x, str) and x == "None":
        return None
    if isinstance(x, str) and str.isdigit(x):
        return int(x)
    if isinstance(x, int):
        return x
    
    raise ArgumentTypeError(f"{x} is not an Integer")







if __name__ == "__main__":

    args = ArgumentParser("encode")
    args.add_argument("--input", action="store", type=path.abspath, required=True)
    args.add_argument("--output", action="store", type=path.abspath, default="./data.json")
    args.add_argument("--text_columns", action="store", nargs="+", type=str, default=[], required=True)       
    args.add_argument("--text_split", action="store_true", default=False)
    args.add_argument("--text_sizes", action="store", nargs="+", type=intornonetype, default=[])
    args.add_argument("--data_columns", action="store", nargs="+", type=str, default=[])
    args.add_argument("--encoder_model", action="store", type=str, default="facebook/dpr-ctx_encoder-multiset-base")
    args.add_argument("--designated_bytes", action="store", type=int, default=500000000)

    args = args.parse_args()
    args.input = "../mbz_extract/extraction.csv"


    if not path.isfile(args.input):
        print("input isnt a file")
        sys.exit(1)
    
    if path.isfile(args.output):
        print("output file already exists")
        sys.exit(1)


    try:

        encoder = OnDemandDPREncoder(args.encoder_model)

        c_chunks = estimate_chunks(args.input, args.designated_bytes, load=0.25)
        data = from_file(args.input, args.input.split(".")[-1], chunk_size=c_chunks)


        for x in data:
            if not all( xx in x for xx in args.text_columns):
                raise ValueError(f"text_columns ({[ xx for xx in args.text_columns if not xx in x ]}) are invalid for inputdata {args.input} ({x.columns.tolist()})")
                
            if not all((xx in x for xx in args.data_columns)):
                raise ValueError(f"data_columns ({[xx for xx in args.data_columns if not xx in x]}) are invalid for inputdata {args.input} ({x.columns.tolist()})")



            if args.text_split or args.text_sizes:
                for i, xx in enumerate(args.text_columns):
                    if args.text_sizes and i < len(args.text_sizes) and args.text_sizes[i]:
                        x[xx] = x[xx].apply(textsplit, args=(args.text_sizes[i], ))
                    elif args.text_sizes and i < len(args.text_sizes) and args.text_sizes[i] == None:
                        pass
                    else:
                        x[xx] = x[xx].apply(textsplit)
                
               
            for xx in args.text_columns:
                x = x.explode(xx, ignore_index=True)
            
    


            text = x[ args.text_columns ].astype(str).apply(lambda x: str.join(" ", x), axis=1)
            data = pd.Series(x[ args.data_columns ].to_dict(orient="records") or [ {} ] * len(x))
            del x
            
            data = pd.DataFrame(
                {
                    "data": pd.Series.combine(data, text, lambda _x, _y: _x | {"text": _y}),
                    "embedding": encoder.vectorize(text.tolist())
                }
            )
            data.to_json(args.output, mode="a", lines=True, orient="records")
            del text
            del data
            


    except Exception as e:
        print(f"Failed: {e}")

        sys.exit(1)