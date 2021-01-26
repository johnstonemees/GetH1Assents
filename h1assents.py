#!/usr/bin/python3

import sys
import requests
import base64
import json
import difflib
import pysnooper
import os

def init_h1_cookies(hostsession):
	cookies = {"Content-type": "application/json", 
	"Host": "hackerone.com",
	"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
	"Accept": "*/*"}
	cookies.update(hostsession)
	return cookies

def get_h1_token(h1_cookies):
	print ("start get_h1_token")
	h1_cookies = {"Cookie": "__Host-session="+h1_cookies}
	cookies = init_h1_cookies(h1_cookies)
	resp = requests.get('https://hackerone.com/current_user/graphql_token',headers=cookies)
	jsn = json.loads(resp.text)
	if (jsn['graphql_token'] == "----"):
		print ("Error: The supplied HackerOne __Host-session token appears to be invalid.Send a notifycation to reset the __Host-session")
		#sendmessage_slack(message)
		exit(1)
	print ("end get_h1_token")
	return jsn['graphql_token']

def get_h1_allprograms(token):
	print ("start get_h1_allprograms")
	need_compare = 1
	h1_xauth_token = {"X-Auth-Token":token}
	cookies = init_h1_cookies(h1_xauth_token)
	get_h1_programs(public_query,cookies)
	get_h1_programs(private_query,cookies)

	if not len(all_teams):
		return
	#write all teams to the local file
	if not os.path.isfile('./h1programs.txt'): 
		os.system("touch h1programs.txt")
		need_compare = 0
		with open("h1programs.txt", "r+") as programs:
			for team in all_teams:
				programs.write(team+"\n")
	else:
		os.system("touch h1programs_tmp.txt")
		with open("h1programs_tmp.txt", "r+") as programs:
			for team in all_teams:
				programs.write(team+"\n")
	if need_compare:
		compare_diff("h1programs","h1programs_tmp")
		os.system("rm h1programs.txt")
		os.system("mv h1programs_tmp.txt h1programs.txt")

	#retrive all the assets
	for team in all_teams:
		print (team)
		get_h1_assets(cookies, team)

	#write all assent to file
	if os.path.isfile('./all_assents.txt'): #check if programs.txt exist, if not create a new one
		os.system("rm all_assents.txt")
	os.system("touch all_assents.txt")
	if len(all_assents):
		with open("all_assents.txt", "r+") as assents:
			for assent in all_assents:
				print (assent)
				assents.write(assent+"\n")
	print ("end get_h1_allprograms")

def get_h1_assets(cookies,handle):
	print ("start get_h1_assets")
	GET_ASSETS_QUERY = "eyJxdWVyeSI6InF1ZXJ5IFRlYW1fYXNzZXRzKCRmaXJzdF8wOkludCEpIHtxdWVyeSB7aWQsLi4uRjB9fSBmcmFnbWVudCBGMCBvbiBRdWVyeSB7bWUge19tZW1iZXJzaGlwX0E6bWVtYmVyc2hpcCh0ZWFtX2hhbmRsZTpcIl9fUkVQTEFDRU1FX19cIikge3Blcm1pc3Npb25zLGlkfSxpZH0sX3RlYW1fQTp0ZWFtKGhhbmRsZTpcIl9fUkVQTEFDRU1FX19cIikge2hhbmRsZSxfc3RydWN0dXJlZF9zY29wZV92ZXJzaW9uc19BOnN0cnVjdHVyZWRfc2NvcGVfdmVyc2lvbnMoYXJjaGl2ZWQ6ZmFsc2UpIHttYXhfdXBkYXRlZF9hdH0sX3N0cnVjdHVyZWRfc2NvcGVzX0I6c3RydWN0dXJlZF9zY29wZXMoZmlyc3Q6JGZpcnN0XzAsYXJjaGl2ZWQ6ZmFsc2UsZWxpZ2libGVfZm9yX3N1Ym1pc3Npb246dHJ1ZSkge2VkZ2VzIHtub2RlIHtpZCxhc3NldF90eXBlLGFzc2V0X2lkZW50aWZpZXIscmVuZGVyZWRfaW5zdHJ1Y3Rpb24sbWF4X3NldmVyaXR5LGVsaWdpYmxlX2Zvcl9ib3VudHl9LGN1cnNvcn0scGFnZUluZm8ge2hhc05leHRQYWdlLGhhc1ByZXZpb3VzUGFnZX19LF9zdHJ1Y3R1cmVkX3Njb3Blc19DOnN0cnVjdHVyZWRfc2NvcGVzKGZpcnN0OiRmaXJzdF8wLGFyY2hpdmVkOmZhbHNlLGVsaWdpYmxlX2Zvcl9zdWJtaXNzaW9uOmZhbHNlKSB7ZWRnZXMge25vZGUge2lkLGFzc2V0X3R5cGUsYXNzZXRfaWRlbnRpZmllcixyZW5kZXJlZF9pbnN0cnVjdGlvbn0sY3Vyc29yfSxwYWdlSW5mbyB7aGFzTmV4dFBhZ2UsaGFzUHJldmlvdXNQYWdlfX0saWR9LGlkfSIsInZhcmlhYmxlcyI6eyJmaXJzdF8wIjo1MDB9fQ=="
	query = base64.b64decode(GET_ASSETS_QUERY)
	query = query.replace(b"__REPLACEME__", handle.encode())

	resp = requests.post('https://hackerone.com/graphql',headers=cookies,data=query)
	data = json.loads(resp.text)

	for elem in data["data"]["query"]["_team_A"]["_structured_scopes_B"]["edges"]:
		if elem["node"]["asset_type"] == "URL":
			if elem["node"]["eligible_for_bounty"] == True:
				all_assents.append(str(elem["node"]["asset_identifier"]))
	print ("end get_h1_assets")


def get_h1_programs(query_string,cookies):
	print ("start get_h1_programs")
	last_cursor = ""
	while(1):
		query_string["variables"]["cursor"] = last_cursor
		programs_resp = requests.post('https://hackerone.com/graphql',headers=cookies,data=json.dumps(query_string))
		programs_data = json.loads(programs_resp.text)

		if len(programs_data["data"]["teams"]["edges"]) == 0:
			break
		print ("found a programs")
		last_cursor = programs_data["data"]["teams"]["pageInfo"]["endCursor"]
		for edge in programs_data["data"]["teams"]["edges"]:
			handle = edge["node"]["handle"]
			all_teams.append(handle)
	print ("end get_h1_programs")

def compare_diff(compare_name1,compare_name2):
	print ("start compare_diff")
	result = []
	try:
		file1 = open("./"+compare_name1+".txt",'r')
		file2 = open("./"+compare_name2+".txt",'r')
		diff = difflib.ndiff(file1.readlines(), file2.readlines())
		changes = [l for l in diff if l.startswith('+ ')] #check if there are new items/subdomains
		newdiff = []
		if len(changes):
			send_to_slack("No new programs found!")
			return
		for c in changes:
			c = c \
				.replace('+ ', '') \
				.replace('*.', '') \
				.replace('\n', '')
			result.append(c)
			result = list(set(result)) #remove duplicates
		#send_to_slack(result)
	except:pass
	print ("end compare_diff")

def send_to_slack(message):
	print (result)

if __name__ == "__main__":
	if (len(sys.argv) != 2 and len(sys.argv) != 3):
		print ("Usage: h1assets <Your HackerOne __Host-session Token>")
		exit(1)
	
	host_session_token = sys.argv[1]
	all_teams = []
	all_assents = []

	#start for init the graphql query,public program and private program query string
	PRIV_PROG_QUERY = "eyJvcGVyYXRpb25OYW1lIjoiTXlQcm9ncmFtc1F1ZXJ5IiwidmFyaWFibGVzIjp7IndoZXJlIjp7Il9hbmQiOlt7Il9vciI6W3sic3VibWlzc2lvbl9zdGF0ZSI6eyJfZXEiOiJvcGVuIn19LHsic3VibWlzc2lvbl9zdGF0ZSI6eyJfZXEiOiJhcGlfb25seSJ9fSx7InN1Ym1pc3Npb25fc3RhdGUiOnsiX2lzX251bGwiOnRydWV9fV19LHsiX29yIjpbeyJfYW5kIjpbeyJfb3IiOlt7ImJvb2ttYXJrZWRfdGVhbV91c2VycyI6eyJpc19tZSI6dHJ1ZX19LHsid2hpdGVsaXN0ZWRfaGFja2VycyI6eyJpc19tZSI6dHJ1ZX19XX0seyJzdGF0ZSI6eyJfZXEiOiJzb2Z0X2xhdW5jaGVkIn19XX0seyJfYW5kIjpbeyJfb3IiOlt7ImJvb2ttYXJrZWRfdGVhbV91c2VycyI6eyJpc19tZSI6dHJ1ZX19LHsicmVwb3J0ZXJzIjp7ImlzX21lIjp0cnVlfX1dfSx7Il9vciI6W3sic3RhdGUiOnsiX2VxIjoicHVibGljX21vZGUifX0seyJleHRlcm5hbF9wcm9ncmFtIjp7ImlkIjp7Il9pc19udWxsIjpmYWxzZX19fV19XX1dfV19LCJjb3VudCI6MjUsIm9yZGVyQnkiOm51bGwsInNlY3VyZU9yZGVyQnkiOnsic3RhcnRlZF9hY2NlcHRpbmdfYXQiOnsiX2RpcmVjdGlvbiI6IkRFU0MifX0sImN1cnNvciI6IiJ9LCJxdWVyeSI6InF1ZXJ5IE15UHJvZ3JhbXNRdWVyeSgkY3Vyc29yOiBTdHJpbmcsICRjb3VudDogSW50LCAkd2hlcmU6IEZpbHRlcnNUZWFtRmlsdGVySW5wdXQsICRvcmRlckJ5OiBUZWFtT3JkZXJJbnB1dCwgJHNlY3VyZU9yZGVyQnk6IEZpbHRlcnNUZWFtRmlsdGVyT3JkZXIpIHtcbiAgbWUge1xuICAgIGlkXG4gICAgLi4uTXlIYWNrZXJPbmVTdWJIZWFkZXJcbiAgICBfX3R5cGVuYW1lXG4gIH1cbiAgdGVhbXMoZmlyc3Q6ICRjb3VudCwgYWZ0ZXI6ICRjdXJzb3IsIG9yZGVyX2J5OiAkb3JkZXJCeSwgc2VjdXJlX29yZGVyX2J5OiAkc2VjdXJlT3JkZXJCeSwgd2hlcmU6ICR3aGVyZSkge1xuICAgIHBhZ2VJbmZvIHtcbiAgICAgIGVuZEN1cnNvclxuICAgICAgaGFzTmV4dFBhZ2VcbiAgICAgIF9fdHlwZW5hbWVcbiAgICB9XG4gICAgZWRnZXMge1xuICAgICAgY3Vyc29yXG4gICAgICBub2RlIHtcbiAgICAgICAgaWRcbiAgICAgICAgaGFuZGxlXG4gICAgICAgIG5hbWVcbiAgICAgICAgY3VycmVuY3lcbiAgICAgICAgdGVhbV9wcm9maWxlX3BpY3R1cmU6IHByb2ZpbGVfcGljdHVyZShzaXplOiBtZWRpdW0pXG4gICAgICAgIHN1Ym1pc3Npb25fc3RhdGVcbiAgICAgICAgdHJpYWdlX2FjdGl2ZVxuICAgICAgICBzdGF0ZVxuICAgICAgICBzdGFydGVkX2FjY2VwdGluZ19hdFxuICAgICAgICBudW1iZXJfb2ZfcmVwb3J0c19mb3JfdXNlclxuICAgICAgICBudW1iZXJfb2ZfdmFsaWRfcmVwb3J0c19mb3JfdXNlclxuICAgICAgICBib3VudHlfZWFybmVkX2Zvcl91c2VyXG4gICAgICAgIGxhc3RfaW52aXRhdGlvbl9hY2NlcHRlZF9hdF9mb3JfdXNlclxuICAgICAgICBib29rbWFya2VkXG4gICAgICAgIGV4dGVybmFsX3Byb2dyYW0ge1xuICAgICAgICAgIGlkXG4gICAgICAgICAgX190eXBlbmFtZVxuICAgICAgICB9XG4gICAgICAgIC4uLlRlYW1MaW5rV2l0aE1pbmlQcm9maWxlXG4gICAgICAgIC4uLlRlYW1UYWJsZUF2ZXJhZ2VCb3VudHlcbiAgICAgICAgLi4uVGVhbVRhYmxlTWluaW11bUJvdW50eVxuICAgICAgICAuLi5UZWFtVGFibGVSZXNvbHZlZFJlcG9ydHNcbiAgICAgICAgX190eXBlbmFtZVxuICAgICAgfVxuICAgICAgX190eXBlbmFtZVxuICAgIH1cbiAgICBfX3R5cGVuYW1lXG4gIH1cbn1cblxuZnJhZ21lbnQgVGVhbUxpbmtXaXRoTWluaVByb2ZpbGUgb24gVGVhbSB7XG4gIGlkXG4gIGhhbmRsZVxuICBuYW1lXG4gIF9fdHlwZW5hbWVcbn1cblxuZnJhZ21lbnQgVGVhbVRhYmxlQXZlcmFnZUJvdW50eSBvbiBUZWFtIHtcbiAgaWRcbiAgY3VycmVuY3lcbiAgYXZlcmFnZV9ib3VudHlfbG93ZXJfYW1vdW50XG4gIGF2ZXJhZ2VfYm91bnR5X3VwcGVyX2Ftb3VudFxuICBfX3R5cGVuYW1lXG59XG5cbmZyYWdtZW50IFRlYW1UYWJsZU1pbmltdW1Cb3VudHkgb24gVGVhbSB7XG4gIGlkXG4gIGN1cnJlbmN5XG4gIGJhc2VfYm91bnR5XG4gIF9fdHlwZW5hbWVcbn1cblxuZnJhZ21lbnQgVGVhbVRhYmxlUmVzb2x2ZWRSZXBvcnRzIG9uIFRlYW0ge1xuICBpZFxuICByZXNvbHZlZF9yZXBvcnRfY291bnRcbiAgX190eXBlbmFtZVxufVxuXG5mcmFnbWVudCBNeUhhY2tlck9uZVN1YkhlYWRlciBvbiBVc2VyIHtcbiAgaWRcbiAgaGFzX2NoZWNrbGlzdF9jaGVja19yZXNwb25zZXNcbiAgc29mdF9sYXVuY2hfaW52aXRhdGlvbnMoc3RhdGU6IG9wZW4pIHtcbiAgICB0b3RhbF9jb3VudFxuICAgIF9fdHlwZW5hbWVcbiAgfVxuICBfX3R5cGVuYW1lXG59XG4ifQ=="
	private_query = json.loads(base64.b64decode(PRIV_PROG_QUERY).decode('utf-8'))
	PUB_PROG_QUERY = "eyJvcGVyYXRpb25OYW1lIjoiRGlyZWN0b3J5UXVlcnkiLCJ2YXJpYWJsZXMiOnsid2hlcmUiOnsiX2FuZCI6W3siX29yIjpbeyJvZmZlcnNfYm91bnRpZXMiOnsiX2VxIjp0cnVlfX0seyJleHRlcm5hbF9wcm9ncmFtIjp7Im9mZmVyc19yZXdhcmRzIjp7Il9lcSI6dHJ1ZX19fV19LHsic3RydWN0dXJlZF9zY29wZXMiOnsiX2FuZCI6W3siYXNzZXRfdHlwZSI6eyJfZXEiOiJVUkwifX0seyJpc19hcmNoaXZlZCI6ZmFsc2V9XX19LHsiX29yIjpbeyJzdWJtaXNzaW9uX3N0YXRlIjp7Il9lcSI6Im9wZW4ifX0seyJzdWJtaXNzaW9uX3N0YXRlIjp7Il9lcSI6ImFwaV9vbmx5In19LHsiZXh0ZXJuYWxfcHJvZ3JhbSI6e319XX0seyJfbm90Ijp7ImV4dGVybmFsX3Byb2dyYW0iOnt9fX0seyJfb3IiOlt7Il9hbmQiOlt7InN0YXRlIjp7Il9uZXEiOiJzYW5kYm94ZWQifX0seyJzdGF0ZSI6eyJfbmVxIjoic29mdF9sYXVuY2hlZCJ9fV19LHsiZXh0ZXJuYWxfcHJvZ3JhbSI6e319XX1dfSwiZmlyc3QiOjI1LCJzZWN1cmVPcmRlckJ5Ijp7InN0YXJ0ZWRfYWNjZXB0aW5nX2F0Ijp7Il9kaXJlY3Rpb24iOiJERVNDIn19LCJjdXJzb3IiOiIifSwicXVlcnkiOiJxdWVyeSBEaXJlY3RvcnlRdWVyeSgkY3Vyc29yOiBTdHJpbmcsICRzZWN1cmVPcmRlckJ5OiBGaWx0ZXJzVGVhbUZpbHRlck9yZGVyLCAkd2hlcmU6IEZpbHRlcnNUZWFtRmlsdGVySW5wdXQpIHtcbiAgbWUge1xuICAgIGlkXG4gICAgZWRpdF91bmNsYWltZWRfcHJvZmlsZXNcbiAgICBoMV9wZW50ZXN0ZXJcbiAgICBfX3R5cGVuYW1lXG4gIH1cbiAgdGVhbXMoZmlyc3Q6IDI1LCBhZnRlcjogJGN1cnNvciwgc2VjdXJlX29yZGVyX2J5OiAkc2VjdXJlT3JkZXJCeSwgd2hlcmU6ICR3aGVyZSkge1xuICAgIHBhZ2VJbmZvIHtcbiAgICAgIGVuZEN1cnNvclxuICAgICAgaGFzTmV4dFBhZ2VcbiAgICAgIF9fdHlwZW5hbWVcbiAgICB9XG4gICAgZWRnZXMge1xuICAgICAgbm9kZSB7XG4gICAgICAgIGlkXG4gICAgICAgIGJvb2ttYXJrZWRcbiAgICAgICAgLi4uVGVhbVRhYmxlUmVzb2x2ZWRSZXBvcnRzXG4gICAgICAgIC4uLlRlYW1UYWJsZUF2YXRhckFuZFRpdGxlXG4gICAgICAgIC4uLlRlYW1UYWJsZUxhdW5jaERhdGVcbiAgICAgICAgLi4uVGVhbVRhYmxlTWluaW11bUJvdW50eVxuICAgICAgICAuLi5UZWFtVGFibGVBdmVyYWdlQm91bnR5XG4gICAgICAgIC4uLkJvb2ttYXJrVGVhbVxuICAgICAgICBfX3R5cGVuYW1lXG4gICAgICB9XG4gICAgICBfX3R5cGVuYW1lXG4gICAgfVxuICAgIF9fdHlwZW5hbWVcbiAgfVxufVxuXG5mcmFnbWVudCBUZWFtVGFibGVSZXNvbHZlZFJlcG9ydHMgb24gVGVhbSB7XG4gIGlkXG4gIHJlc29sdmVkX3JlcG9ydF9jb3VudFxuICBfX3R5cGVuYW1lXG59XG5cbmZyYWdtZW50IFRlYW1UYWJsZUF2YXRhckFuZFRpdGxlIG9uIFRlYW0ge1xuICBpZFxuICBwcm9maWxlX3BpY3R1cmUoc2l6ZTogbWVkaXVtKVxuICBuYW1lXG4gIGhhbmRsZVxuICBzdWJtaXNzaW9uX3N0YXRlXG4gIHRyaWFnZV9hY3RpdmVcbiAgcHVibGljbHlfdmlzaWJsZV9yZXRlc3RpbmdcbiAgc3RhdGVcbiAgZXh0ZXJuYWxfcHJvZ3JhbSB7XG4gICAgaWRcbiAgICBfX3R5cGVuYW1lXG4gIH1cbiAgLi4uVGVhbUxpbmtXaXRoTWluaVByb2ZpbGVcbiAgX190eXBlbmFtZVxufVxuXG5mcmFnbWVudCBUZWFtTGlua1dpdGhNaW5pUHJvZmlsZSBvbiBUZWFtIHtcbiAgaWRcbiAgaGFuZGxlXG4gIG5hbWVcbiAgX190eXBlbmFtZVxufVxuXG5mcmFnbWVudCBUZWFtVGFibGVMYXVuY2hEYXRlIG9uIFRlYW0ge1xuICBpZFxuICBzdGFydGVkX2FjY2VwdGluZ19hdFxuICBfX3R5cGVuYW1lXG59XG5cbmZyYWdtZW50IFRlYW1UYWJsZU1pbmltdW1Cb3VudHkgb24gVGVhbSB7XG4gIGlkXG4gIGN1cnJlbmN5XG4gIGJhc2VfYm91bnR5XG4gIF9fdHlwZW5hbWVcbn1cblxuZnJhZ21lbnQgVGVhbVRhYmxlQXZlcmFnZUJvdW50eSBvbiBUZWFtIHtcbiAgaWRcbiAgY3VycmVuY3lcbiAgYXZlcmFnZV9ib3VudHlfbG93ZXJfYW1vdW50XG4gIGF2ZXJhZ2VfYm91bnR5X3VwcGVyX2Ftb3VudFxuICBfX3R5cGVuYW1lXG59XG5cbmZyYWdtZW50IEJvb2ttYXJrVGVhbSBvbiBUZWFtIHtcbiAgaWRcbiAgYm9va21hcmtlZFxuICBfX3R5cGVuYW1lXG59XG4ifQ=="
	public_query = json.loads(base64.b64decode(PUB_PROG_QUERY).decode('utf-8'))
	
	#start for init the cookies and token from H1
	h1_graphql_token = get_h1_token(host_session_token)

	#Start for retrive the programs from H1
	get_h1_allprograms(h1_graphql_token)
