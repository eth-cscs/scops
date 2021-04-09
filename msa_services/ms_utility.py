from flask import request, jsonify
from logzero import logger
from token_api import secret
from functools import wraps
import time

def check_apikey(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        apikey = request.headers.get('X-Auth-Token')
        if apikey != secret:
            logger.error("Authentication TOKEN not valid")
            return jsonify(error="Authentication TOKEN not valid"), 401
        return f(*args, **kwargs)
    return wrap

def timing(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        time1 = time.time()
        ret = f(*args, **kwargs)
        time2 = time.time()
        logger.info(f"Timing: {f.__name__} = {round(time2-time1,1)} s")
        return ret
    return wrap
