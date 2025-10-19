# Big problems i had here:
"""
Some wikidata/json responses that contained addresses or phone numbers were hiding in plain text
for that i used regex patterns and mwparserfromhell to find the addresses that's why for some people it may find address and for some it won't
its a massive rabbit hole.
mwparserfromhell is a wiki parser that uses templates
https://mwparserfromhell.readthedocs.io/en/latest/usage.html
i used basic regex before i found out about it and it was hell, i left regex as a fallback if mwparser doesnt return anything.

Some wikidata only had links for addresses of people, like in Dwight Schrute example the raw json text contained a link [[Schrute Farms]]
and i had to create a function to extract links from text that associated with their location and then scan the location link raw text
"""


import requests
import mwparserfromhell

import os
import re
from ratelimit import limits, sleep_and_retry
from collections import defaultdict

from helper_funcs.save_results import *

from dotenv import load_dotenv

load_dotenv(dotenv_path="../../.env")

wikidata_url = "https://www.wikidata.org/w/api.php"
wikipedia_url = "https://en.wikipedia.org/w/api.php"
ru_url = "https://randomuser.me/api"

fandom_wikis = {
    "the_office": "https://theoffice.fandom.com/api.php",
    "simpsons": "https://simpsons.fandom.com/api.php"
}

# no api key, only git link for auth. api's i use dont require api key for read only requests
headers = {
    "User-Agent": f"digital_detective ({os.getenv('USER_AGENT')})"
}
# 1 function call every 2 seconds(rate limit)
@sleep_and_retry
@limits(calls=30,period=60)
def findby_name(name, fandom=None):

    if len(name) < 4:
        print("Invalid name")
        return

    field_sources = {
        "first_name": defaultdict(list),
        "last_name": defaultdict(list),
        "address": defaultdict(list),
        "phone_number": defaultdict(list),
        "description": defaultdict(list)
    }
    
    # wikidata lookup--------------------------------------------------
    params_wd = {
        "action": "wbsearchentities",
        "search": name,
        "language": "en",
        "format": "json",
        "type": "item",
        "limit": 1
    }
    response_wd = requests.get(wikidata_url, params=params_wd, headers=headers)
    data_wd = response_wd.json()
    #print(data_wd)

    wd_first = wd_last = wd_description = wd_address = wd_phone = None

    if data_wd.get("search"):
        top_result = data_wd["search"][0]
        entity_id = top_result["id"]
        label = top_result.get("label", "")
        wd_description = top_result.get("description", "")

        #get first and last name from label
        parts = label.split(" ")
        wd_first = parts[0] if parts else None
        wd_last = " ".join(parts[1:]) if len(parts) > 1 else None
        add_field(field_sources, "first_name", wd_first, "wikidata")
        add_field(field_sources, "last_name", wd_last, "wikidata")

        add_field(field_sources, "description", wd_description, "wikidata")

        #print(top_result)
        wd_address, wd_phone = fetch_wikidata_claims(entity_id)
        add_field(field_sources, "address", wd_address, "wikidata")
        add_field(field_sources, "phone_number", wd_phone, "wikidata")

        #cross-page reference
        text_for_links = " ".join([label, wd_description])
        linked_pages = extract_linked_pages(text_for_links)
        for page in linked_pages:
            linked_text = fetch_page_wikitext(wikidata_url, page)
            addr, phone = extractNumTel(linked_text)
            add_field(field_sources, "address", addr, f"wikidata:{page}")
            add_field(field_sources, "phone_number", phone, f"wikidata:{page}")

    # wikipedia lookup--------------------------------------------------
    params_wp = {
        "action": "query",
        "list": "search",
        "srsearch": name,
        "format": "json"
    }
    response_wp = requests.get(wikipedia_url, params=params_wp, headers=headers)
    data_wp = response_wp.json()
    #print(data_wp)

    if "query" in data_wp and data_wp["query"]["search"]:
        pageid = data_wp["query"]["search"][0]["pageid"]
    
        parse_params = {
            "action": "parse",
            "pageid": pageid,
            "prop": "wikitext",
            "format": "json",
            "redirects": 1
        }
        parse_resp = requests.get(wikipedia_url, params=parse_params, headers=headers)
        parse_data = parse_resp.json()
        wikitext = parse_data.get("parse", {}).get("wikitext", {}).get("*", "")
        wp_first = None 
        wp_last = None

        wp_address, wp_phone = extractNumTel(wikitext)
        # try to get wikipedia first and last name from title
        wp_title = parse_data.get("parse", {}).get("title", "")
        
        if wp_address: add_field(field_sources, "address", wp_address, "wikipedia")
        if wp_phone: add_field(field_sources, "phone_number", wp_phone, "wikipedia")

        linked_pages = extract_linked_pages(wikitext)
        for page in linked_pages:
            linked_text = fetch_page_wikitext(wikipedia_url, page)
            addr, phone = extractNumTel(linked_text)
            if addr: add_field(field_sources, "address", addr, "wikipedia")
            if phone: add_field(field_sources, "phone_number", phone, "wikipedia")

        if wp_title:
            parts = wp_title.split(" ")
            if parts:
                wp_first = parts[0]
                wp_last = " ".join(parts[1:]) if len(parts) > 1 else None
                add_field(field_sources, "first_name", wp_first, "wikipedia")
                if wp_last: add_field(field_sources, "last_name", wp_last, "wikipedia")


    #FANDOM lookup (if you want to add a fandom, add an api link to the top)

    #Loops through fandom wikis, checks if character exists in that wiki, if found extracts data and stop loop
    for show, wiki_url in fandom_wikis.items():
        page_name = name.title().replace(" ", "_")
        params_fandom = {
            "action": "parse",
            "page": page_name,
            "prop": "wikitext|displaytitle",
            "format": "json"
        }
        #print(wiki_url + "?page=" + name.replace(" ", "_"))
        response_fd = requests.get(wiki_url, params=params_fandom, headers=headers)
        if response_fd.ok and "parse" in response_fd.json():
            #print("fd response ok")
            fd_found = show
            data_fd = response_fd.json()
            #print(data_fd)
            wikitext_fd = data_fd.get("parse", {}).get("wikitext", {}).get("*", "")

            linked_pages = extract_linked_pages(wikitext_fd) 

            linked_texts = []
            for lp in linked_pages:
                text = fetch_page_wikitext(wiki_url, lp)
                if text:
                    linked_texts.append(text)
                    #print(f"fetched linked page: {lp}")

            linked_texts.insert(0, wikitext_fd)

            fd_address, fd_phone = extractNumTel(None, extra_texts=linked_texts)
            if fd_address: add_field(field_sources, "address", fd_address, "fandom")
            if fd_phone: add_field(field_sources, "phone_number", fd_phone, "fandom")

            title = data_fd.get("parse", {}).get("title", "")
            if title:
                parts = title.split(" ")
                if parts:
                    add_field(field_sources, "first_name", parts[0], "fandom")
                    if len(parts) > 1:
                        add_field(field_sources, "last_name", " ".join(parts[1:]), "fandom")
            break
    
    #print(fd_address)
    #print(fd_phone)
    """
    #RandomUser Api for fake adress and phone (fallback)    in the end left it commented out
    response_ru = requests.get(ru_url, headers=headers)
    if response_ru.ok:
        user = response_ru.json()["results"][0]
        location = user["location"]
        street = location["street"]
        ru_address = f"{street['name']} {street['number']}, {location['city']}, {location['state']}, {location['country']} {location['postcode']}"
        ru_phone = user["phone"]

        field_sources["address"][ru_address].append("randomuser")
        field_sources["phone_number"][ru_phone].append("randomuser")
    """
    #print(wp_phone)
    #print(wp_address)
    final_results = {}
    source_counts = {}
    for field, values_dict in field_sources.items():
        if not values_dict:
            final_results[field] = None
            source_counts[field] = 0
            continue
        counts = {val: len(srcs) for val, srcs in values_dict.items()}
        best_value = max(counts, key=counts.get)
        final_results[field] = best_value
        source_counts[field] = counts[best_value]

    first = (final_results.get("first_name") or "unknown").lower()
    last = (final_results.get("last_name") or "unknown").lower()
    full = "_".join([first, last])
    
    # end message
    result_output = f"""
    First name: {final_results['first_name'] or 'N/A'} (src: {source_counts['first_name']})
    Last name: {final_results['last_name'] or 'N/A'} (src: {source_counts['last_name']})
    Address: {final_results['address'] or 'N/A'} (src: {source_counts['address']})
    Phone number: {final_results['phone_number'] or 'N/A'} (src: {source_counts['phone_number']})
    Description: {final_results['description'] or 'N/A'} (src: {source_counts['description']})
    """
    # if no values in dict, then only print, dont save
    if all(v is None for v in final_results.values()):
        print(result_output)
    else:
        filename = save_results("n", full, result_output)
        
        print(result_output)
        print(f"    Results written to file: {filename}")
    

# extract address and phone from wikitext using mwparserfromhell using templates provided by library
# scans raw wikitext
def extractNumTel(text, extra_texts=None):
    addresses = []
    phones = []

    def _extract_single(txt):
        addr, phone = None, None
        if not txt:
            return None, None
        try:
            wikicode = mwparserfromhell.parse(txt)
            
            # Scan template
            for template in wikicode.filter_templates():
                name = template.name.strip().lower()
                for param in template.params:
                    pname = str(param.name).strip().lower()
                    pval = clean_wikitext(str(param.value).strip())

                    # check for address in templates
                    if ("address" in pname or "location" in pname or "adress" in name) and is_valid_address(pval):
                        addr = pval
                        #print(f"Found address in template: {addr}")
                    
                    # check for phone in templates
                    if ("phone" in pname or "telephone" in pname or "tel" in pname or "phone" in name) and is_valid_phone(pval):
                        phone = re.sub(r"\D", "", pval)
                        #print(f"Found phone in template: {phone}")

            # fallback regex for plain text
            phone_patterns = [
                r"\[\[Tel:[^\|]+\|([^\]]+)\]\]",
                r"\{\{Phone\|([^\}]+)\}\}",
                r"phone\s*=\s*(.+)",
                r"telephone\s*=\s*(.+)"
            ]
            address_patterns = [
                r'address\s*=\s*([^\n\|\}]+)',
                r'location\s*=\s*([^\n\|\}]+)',
                r'\{\{Address\|([^\}\n]+)\}\}',
                r'\{\{Location\|([^\}\n]+)\}\}'
            ]

            #fallback regex for address
            if not addr:
                for pattern in address_patterns:
                    match = re.search(pattern, txt, re.IGNORECASE)
                    if match:
                        candidate = match.group(1).strip()
                        if is_valid_address(candidate):
                            addr = candidate
                            #print(f"Found address via regex: {addr}")
                            break

            #fallback regex for phone
            if not phone:
                for pattern in phone_patterns:
                    match = re.search(pattern, txt, re.IGNORECASE)
                    if match:
                        candidate = match.group(1).strip()
                        if is_valid_phone(candidate):
                            phone = re.sub(r"\D", "", candidate)
                            #print(f"Found phone via regex: {phone}")
                            break

            # plain text fallback regex for address
            if not addr:
                plain_address_pattern = r'([A-Za-z0-9\s\.,\-]+, [A-Za-z\s]+, [A-Z]{2} \d{5})'
                match = re.search(plain_address_pattern, txt)
                if match:
                    candidate = match.group(1).strip()
                    if is_valid_address(candidate):
                        addr = candidate
                        #print(f"Found address via plain-text regex: {addr}")

        except Exception as e:
            print("mwparserfromhell failed, falling back to regex:", e)

        return addr, phone
    #extract from main page text
    if text:
        addr, phone = _extract_single(text)
        if addr: addresses.append(addr)
        if phone: phones.append(phone)

    # extract from linked pages
    if extra_texts:
        for et in extra_texts:
            laddr, lphone = _extract_single(et)
            if laddr:
                addresses.append(laddr)
            if lphone:
                phones.append(lphone)

    # Pick the longest address if there are many
    final_address = max(addresses, key=len) if addresses else None
    final_phone = phones[0] if phones else None  # pick first valid phone

    # Normalize
    if final_address:
        final_address = " ".join(final_address.split())
    if final_phone:
        final_phone = re.sub(r'\D', '', final_phone)

    return final_address, final_phone

# function to clean address value from wikitext (brackets, symbols and so on)
def clean_wikitext(raw_text):
    if not raw_text:
        return None
    code = mwparserfromhell.parse(raw_text)
    cleaned = code.strip_code()  # removes [[links]] and {{templates}}
    cleaned = re.sub(r"<br\s*/?>", ", ", cleaned)  # replace <br> with commas
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

def add_field(field_sources, field, value, source):
    if not value:
        return
    if field == "phone_number":
        value = re.sub(r'\D', '', value)
        if not is_valid_phone(value):
            return
    elif field == "address":
        value = clean_wikitext(value)
        if not is_valid_address(value):
            return
    else:
        value = value.strip()
    field_sources[field][value].append(source)

def fetch_wikidata_claims(entity_id):
    url = f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json"
    resp = requests.get(url, headers=headers)
    if resp.ok:
        data = resp.json()
        claims = data["entities"][entity_id]["claims"]
        addr, phone = None, None
        # P969 = address, P1329 = phone
        if "P969" in claims:
            addr = claims["P969"][0]["mainsnak"]["datavalue"]["value"]
        if "P1329" in claims:
            phone = claims["P1329"][0]["mainsnak"]["datavalue"]["value"]
        return addr, phone
    return None, None

# functions to crosspage reference 
# if the json request of a character includes some fields like workplace, residence, etc
# create a new api request with that same link. Links on wiki api's json responses are wrapped with double square brackets
# check for that link for any info.
def extract_linked_pages(wikitext, fields=("workplace", "residence", "location", "born in")):
    linked_pages = []
    for field in fields:
        matches = re.findall(rf"{field}\s*=\s*\[\[([^\]|]+)", wikitext, re.IGNORECASE)
        for m in matches:
            linked_pages.append(m.strip().replace(" ", "_"))
    #print(linked_pages)
    return linked_pages

def fetch_page_wikitext(wiki_url, page):
    params = {
        "action": "parse",
        "page": page,
        "prop": "wikitext",
        "format": "json"
    }
    resp = requests.get(wiki_url, params=params, headers=headers)
    #print(resp.url)
    if resp.ok and "parse" in resp.json():
        return resp.json()["parse"]["wikitext"]["*"]
    #print(f"failed to fetch wikitext for {page}")
    return ""

# checks phone numbers and if they're valid
def is_valid_phone(phone):
    if not phone:
        return False
    digits = re.sub(r"\D", "", phone)
    return len(digits) >= 7

# checks addresses, so we don't get return value of just the city name or etc
def is_valid_address(addr):
    if not addr:
        return False
    return bool(re.search(r"\d{1,5}", addr))
    
    
    