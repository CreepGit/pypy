from bs4 import BeautifulSoup
import requests
import json
import time
import re
import base64
import shutil
from PIL import Image
import threading

base_url = r"https://gbf.wiki"
look_url = r"https://gbf.wiki/Category:Weapons"

weapon_links_out = "out/scrape/gbf_weapons.json"


weapon_links = []

# while True:
#     print()
#     print("Looking at page", look_url)
#     response = requests.get(look_url)
#     if response.status_code != 200:
#         print()
#         print()
#         print()
#         print()
#         print(response)
#         print()
#         print(response.text)
#         print()
#         print()
#         input(">")
#     soup = BeautifulSoup(response.text, features="lxml")

#     a_tags = soup.find("div", {"class": "mw-category"}).findAll("a")

#     for a_tag in a_tags:
#         weapon_links.append(a_tag["href"])
        
#     with open(weapon_links_out, "w") as file:
#         json.dump(weapon_links, file)
    
#     print(f"Wrote {len(weapon_links)} weapon links")

#     next_page_element = soup.find("a", string="next page")
    
#     if next_page_element == None:
#         print("No more")
#         print("Last found was", weapon_links[-5:])
#         input(">")
    
#     look_url = base_url + next_page_element["href"]
    
#     time.sleep(0.4)

####################################################
check_urls_file = "out/scrape/urls_saved.json"
img_out = "out/scrape/gbf_img/"

with open(weapon_links_out, "r") as file:
    data = json.load(file)

with open(check_urls_file, "r") as file:
    checked_urls = json.load(file)

def look_for(name: str, mini: int, maxi: int):
    
    local_checked = [*checked_urls]
    
    for i, url in enumerate(data):
        if i < mini:
            continue
        if i >= maxi:
            continue
        if url in local_checked:
            # print("Already got", url)
            continue
        
        segment = url[1:]
        search_url = f"https://gbf.wiki{url}"
        # print(f"looking ({len(local_checked)}/{len(data)})", search_url)
        
        response1 = requests.get(search_url)
        soup1 = BeautifulSoup(response1.text, features="lxml")
        
        wikitable = soup1.find("div", {"title":"Stats"})
        if not wikitable:
            print("NO WIKITABLE", i)
            continue
        
        tags = ""
        for a in wikitable.find_all("a"): # type: ignore
            try:
                match = re.match(r"/weapon_lists/\w{1,20}/(\w+)", a["href"].lower())
            except KeyError as e:
                print("KEY ERROR", e)
                print(search_url)
                continue
            if match:
                tag = match.group(1)
                tags += "_" + tag 
        
        
        response3 = requests.get(f"https://gbf.wiki/File:{segment}.png")
        soup3 = BeautifulSoup(response3.text, features="lxml")
        
        imgs1 = soup3.find_all("img", {"width": 640})
        
        if not imgs1:
            print("IMAGE MISSING")
            continue
        if len(imgs1) > 1:
            print("TOO MANY IMAGES")
            continue
        
        img1_src = imgs1[0]["src"]
        
        second_look_url = base_url + img1_src
        
        response2 = requests.get(second_look_url)
        response2.raise_for_status()
        
        forged_name = f"{segment}"
        
        local_path = f"out/scrape/gbf_img/{forged_name}{tags}.png"
        with open(local_path, "wb") as file:
            file.write(response2.content)
            # print("SAVED", local_path)
            
        local_checked.append(url)
        checked_urls.append(url)
        # print(name ,"CHECKED ", i)
    print("STOPPED", name)

def thread_starter():
    threads = []
    for thread in (("T1", 0, 600),("T2", 600, 800),("T3", 800, 1000),("T4", 1000, 1200),("T5", 1200, 1400),("T6", 1400, 1600),("T7", 1600, 1800),("T8", 1800, 2000),("T9", 2200, 2400),("T10", 2400, 2500),("T11", 2500, 2600),("T12", 2600, 2700)):
        T = threading.Thread(target=look_for, args=thread)
        T.start()
        threads.append(T)
        time.sleep(0.15)

    def saverFunc():
        local_checked = []
        while True:
            time.sleep(3)
            
            local_checked = local_checked + [*checked_urls]
            local_checked_set = set(local_checked)
            local_checked = list(local_checked_set)
            
            print("Saver: Saving",len(local_checked),"values")
                
            with open(check_urls_file, "w") as file:
                json.dump(local_checked, file, indent=2)

    saver = threading.Thread(target=saverFunc)
    saver.start()

thread_starter()

def main():
    for i, url in enumerate(data):
        if url in checked_urls:
            print("Already got", url)
            continue
        
        if i < 1600:
            continue
        
        segment = url[1:]
        search_url = f"https://gbf.wiki{url}"
        print(f"looking ({len(checked_urls)}/{len(data)})", search_url)
        
        response1 = requests.get(search_url)
        soup1 = BeautifulSoup(response1.text, features="lxml")
        
        wikitable = soup1.find("div", {"title":"Stats"})
        if not wikitable:
            print("NO WIKITABLE")
            continue
        
        tags = ""
        for a in wikitable.find_all("a"): # type: ignore
            try:
                match = re.match(r"/weapon_lists/\w{1,20}/(\w+)", a["href"].lower())
            except KeyError:
                match = None
            if match:
                tag = match.group(1)
                tags += "_" + tag 
        
        
        response3 = requests.get(f"https://gbf.wiki/File:{segment}.png")
        soup3 = BeautifulSoup(response3.text, features="lxml")
        
        imgs1 = soup3.find_all("img", {"width": 640})
        
        if not imgs1:
            print("IMAGE MISSING")
            continue
        if len(imgs1) > 1:
            print("TOO MANY IMAGES")
            input(">")
        
        img1_src = imgs1[0]["src"]
        
        second_look_url = base_url + img1_src
        
        response2 = requests.get(second_look_url)
        response2.raise_for_status()
        
        forged_name = f"{segment}"
        
        local_path = f"out/scrape/gbf_img/{forged_name}{tags}.png"
        with open(local_path, "wb") as file:
            file.write(response2.content)
            print("SAVED", i, local_path)
            
        checked_urls.append(url)
        with open(check_urls_file, "w") as file:
            json.dump(checked_urls, file, indent=2)
            
        time.sleep(0.3)
        print()
    print("STOPPED")
