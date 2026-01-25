
__version__ = '0.0.1'

import frappe
from frappe.utils import connections

# Monkey patch to handle the modern Redis URL in old v13
def patched_check_redis(redis_services):
    import redis
    status = {}
    for service in redis_services:
        url = frappe.conf.get(service)
        if not url: continue
        
        # This is the logic that fails in v13; we make it smarter
        try:
            # Strip protocol and split safely
            clean_url = url.replace("redis://", "").replace("rediss://", "")
            parts = clean_url.split(":")
            host = parts[0]
            port = parts[1] if len(parts) > 1 else 6379
            
            r = redis.Redis(host=host, port=port, decode_responses=True)
            r.ping()
            status[service] = "OK"
        except Exception:
            status[service] = "Failed"
    return status

# Apply the patch
connections.check_redis = patched_check_redis