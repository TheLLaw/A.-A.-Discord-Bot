import requests
import pickle
import zipfile
import os
import json
import sqlite3
import time

def main():
    print("This should be executed manually! This is a program that updates weapons.json SHOULD NOT BE GIVEN TO ANYONE")
    get_manifest()
    dict = build_dict()
    with open("weapons.json", "w") as f:
        json.dump(dict, f)
    os.remove("MANZIP")
    os.remove("Manifest.content")
    print("Done")
    time.sleep(15)


def get_manifest():
    manifest_url = 'http://www.bungie.net/Platform/Destiny2/Manifest/'
    #get the manifest location from the json
    r = requests.get(manifest_url)
    manifest = r.json()
    mani_url = 'http://www.bungie.net'+manifest['Response']['mobileWorldContentPaths']['en']
    #Download the file, write it to MANZIP
    r = requests.get(mani_url)
    with open("MANZIP", "wb") as zip:
        zip.write(r.content)
    #Extract the file contents, and rename the extracted file
    # to 'Manifest.content'
    with zipfile.ZipFile('MANZIP') as zip:
        name = zip.namelist()
        zip.extractall()
    os.rename(name[0], 'Manifest.content')


def build_dict():
	hash_dict = {"DestinyInventoryItemDefinition": "itemHash"}
	con = sqlite3.connect('manifest.content')
	cur = con.cursor()
	for table_name in hash_dict.keys():
		#get a list of all the jsons from the table
		cur.execute('SELECT json from '+table_name)
		#this returns a list of tuples: the first item in each tuple is our json
		items = cur.fetchall()
		#create a list of jsons
		item_jsons = [json.loads(item[0]) for item in items]
		#create a dictionary with the hashes as keys
		#and the jsons as values
		item_dict = {}
		hash = hash_dict[table_name]
		for item in item_jsons:
			itemHash = item["hash"]
			item_dict[itemHash] = item["inventory"]
		return item_dict


if __name__ == "__main__":
    main()