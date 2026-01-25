import frappe
from frappe.utils import connections

def apply_redis_patch():
    # Only patch if we are on a version that needs it
    try:
        from redis import Redis
        original_check_redis = connections.check_redis

        def patched_check_redis(redis_services):
            status = {}
            for service in redis_services:
                url = frappe.conf.get(service)
                if not url: continue
                try:
                    # Logic to handle redis:// or rediss://
                    clean_url = url.replace("redis://", "").replace("rediss://", "")
                    # Split from the right to get the port correctly
                    parts = clean_url.split(":")
                    host = parts[-2].replace("//", "")
                    port = int(parts[-1])
                    
                    r = Redis(host=host, port=port, decode_responses=True)
                    r.ping()
                    status[service] = "OK"
                except Exception:
                    status[service] = "Failed"
            return status

        connections.check_redis = patched_check_redis
    except Exception:
        pass