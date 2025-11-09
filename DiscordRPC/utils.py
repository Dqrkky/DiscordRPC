import json

def pretty(obj :dict=None):
    if obj == None or isinstance(obj, dict) == False:  # noqa: E711, E712
        return
    return json.dumps(
        obj=obj,
        indent=4,
        ensure_ascii=False
    )

def log(obj :dict=None):
    if obj == None or isinstance(obj, dict) == False:  # noqa: E711, E712
        return
    print(pretty(
        obj=obj
    ))