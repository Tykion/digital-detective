# No problems here, very straightforward

import requests
import os

from helper_funcs.save_results import *

from ratelimit import limits, sleep_and_retry
from dotenv import load_dotenv

load_dotenv()

# https://ipinfo.io/{IP}/json -- ipinfo.io
# http://ip-api.com/json/{IP} -- ip
# https://ipwhois.app/json/{IP}

headers = {
    "User-Agent": f"digital_detective ({os.getenv('USER_AGENT')})"
}

@sleep_and_retry
@limits(calls=30,period=60)
def findby_ip(ip):
    if len(ip) < 7:
        print("Invalid ip")
        return
    
    #safe handling
    final_ip = None
    final_isp = None
    final_location = None
    #source 1
    resp1 = requests.get(f"https://ipinfo.io/{ip}/json", headers=headers)
    data1 = resp1.json()

    # check if ip is valid through first api, if it works it should work in other api's as well
    if ("error" in data1):
        print("N/A results or Invalid Ip adress provided")
        return
    
    resp1_ip = data1["ip"]
    resp1_ISP = data1["org"]
    resp1_location = data1["loc"]
    #print(resp1_ip, resp1_ISP, resp1_location)

    #source 2
    resp2 = requests.get(f"http://ip-api.com/json/{ip}", headers=headers)
    data2 = resp2.json()
    resp2_ip = data2["query"]
    resp2_ISP = data2["as"]
    resp2_lat = data2["lat"]
    resp2_lon = data2["lon"]
    resp2_location = f"{resp2_lat},{resp2_lon}"
    #print(resp2_ip, resp2_ISP, resp2_location)

    #source 3
    resp3 = requests.get(f"https://ipwhois.app/json/{ip}")
    data3 = resp3.json()
    resp3_ip = data3["ip"]
    resp3_asn = data3["asn"]
    resp3_org = data3["org"]
    resp3_ISP = f"{resp3_asn} {resp3_org}"
    resp3_lat = data3["latitude"]
    resp3_lon = data3["longitude"]
    resp3_location = f"{resp3_lat},{resp3_lon}"


    final_ip = compareResult(resp1_ip, resp2_ip, resp3_ip)
    final_isp = compareResult(resp1_ISP, resp2_ISP, resp3_ISP)
    final_location = compareResult(resp1_location, resp2_location, resp3_location)
    
    final_output = f"""
    IP: {final_ip}
    ISP: {final_isp}
    Location: {final_location}
    """
    filename = save_results("ip", ip, final_output)
    
    print(final_output)
    print(f"    Results written to fie: {filename}")
    

#dynamically compare results of the fields
def compareResult(*results):
    # filter out empty results
    filtered = [r for r in results if r is not None]

    if not filtered:
        return None

    if all(r == filtered[0] for r in filtered):
        return filtered[0]

    #return a summary showing all sources if any mismatch happends
    mismatch_summary = " / ".join(f"source{i+1}: {v}" for i, v in enumerate(filtered))
    return f"{mismatch_summary}, mismatch"

