from bs4 import BeautifulSoup
from base64 import b64decode
from urllib.parse import urlparse
import concurrent.futures
import requests
import copy
import sys
import re


post_id = " "
data_dict = {}
main_dict = {}
client = requests.Session() 
DDL_REGEX = re.compile(r"DDL\(([^),]+)\, (([^),]+)), (([^),]+)), (([^),]+))\)")
POST_ID_REGEX =  re.compile(r'"postId":"(\d+)"')
DOWNLOAD_BASE64_REGEX = re.compile(r"openInNewTab\(([^),]+\)"")")
EMPTY_CHECK_REGEX = re.compile(r"Nothing to see here.")
headers = {"x-requested-with": "XMLHttpRequest", "referer": "https://animekaizoku.com"}
ANCHOR_URL = 'https://www.google.com/recaptcha/api2/anchor?ar=1&k=6Lcr1ncUAAAAAH3cghg6cOTPGARa8adOf-y9zv2x&co=aHR0cHM6Ly9vdW8uaW86NDQz&hl=en&v=1B_yv3CBEV10KtI2HJ6eEXhJ&size=invisible&cb=4xnsug1vufyr'


def RecaptchaV3(ANCHOR_URL):
	url_base = 'https://www.google.com/recaptcha/'
	post_data = "v={}&reason=q&c={}&k={}&co={}"
	client = requests.Session()
	client.headers.update({
	    'content-type': 'application/x-www-form-urlencoded'
	})
	matches = re.findall('([api2|enterprise]+)\/anchor\?(.*)', ANCHOR_URL)[0]
	url_base += matches[0]+'/'
	params = matches[1]
	res = client.get(url_base+'anchor', params=params)
	token = re.findall(r'"recaptcha-token" value="(.*?)"', res.text)[0]
	params = dict(pair.split('=') for pair in params.split('&'))
	post_data = post_data.format(params["v"], token, params["k"], params["co"])
	res = client.post(url_base+'reload', params=f'k={params["k"]}', data=post_data)
	answer = re.findall(r'"rresp","(.*?)"', res.text)[0]    
	return answer
	
	
def ouo_bypass(url):
	client = requests.Session()
	tempurl = url.replace("ouo.press", "ouo.io")
	
	p = urlparse(tempurl)
	id = tempurl.split('/')[-1]    
	res = client.get(tempurl)
	
	next_url = f"{p.scheme}://{p.hostname}/go/{id}"
	for _ in range(2):
	    if res.headers.get('Location'):
	        break
	    bs4 = BeautifulSoup(res.content, 'html.parser')
	    inputs = bs4.form.findAll("input", {"name": re.compile(r"token$")})
	    data = { input.get('name'): input.get('value') for input in inputs }        
	    ans = RecaptchaV3(ANCHOR_URL)
	    data['x-token'] = ans
	    
	    h = {
	        'content-type': 'application/x-www-form-urlencoded'
	    }        
	    res = client.post(next_url, data=data, headers=h, allow_redirects=False)
	    next_url = f"{p.scheme}://{p.hostname}/xreallcygo/{id}"
	return res.headers.get('Location')
	
def dictionary_decrypter():
	for key in main_dict:
		print(f"--------------------------------------{key}-------------------------------------\n")
		dict_data = main_dict[key]
		
		if bool(dict_data) == 0:
			print(f"No links found in {key}.")
			
		else:
			for y in dict_data:
				print(f"▪︎ {y}")
				for i in dict_data[y]:
					try: print(f"{i[0]} : {i[1]}")
					except: pass
			print("\n")
	
				
			
def DDL_DECRYPTER(match):
	payload_data = match.group(0).split("DDL(")[1].replace(")", "").split(",")
	return {
	       "action" : "DDL",
	       "post_id": post_id,
	       "div_id": payload_data[0].strip(),
	       "tab_id": payload_data[1].strip(),
	       "num"   : payload_data[2].strip(),
	       "folder" : payload_data[3].strip(),
	}
	

def ouo_extracter(dict_key, button, loop_soup):          
	try:
		ouo_encrypt = DOWNLOAD_BASE64_REGEX.search(str(loop_soup)).group(0).strip().split('"')[1]
		ouo_decrypt = b64decode(ouo_encrypt).decode("utf-8").strip()
		
		try: decrypted_link= ouo_bypass(ouo_decrypt)
		except: decrypted_link = ouo_decrypt
		
		data_dict[dict_key].append([button.text.strip(), decrypted_link.strip()])  
		   	
	except: looper(dict_key, str(button))
		  	
	
def looper(dict_key, click):
	x = DDL_DECRYPTER(DDL_REGEX.search(click))
	new_num = x["num"].split("'")[1]
	x["num"] = new_num
	   
	response = client.post("https://animekaizoku.com/wp-admin/admin-ajax.php", headers=headers, data=x)  
	loop_soup = BeautifulSoup(response.text, "html.parser")
	downloadbutton = loop_soup.find_all(class_="downloadbutton")
	
	with concurrent.futures.ThreadPoolExecutor() as executor:
		[executor.submit(ouo_extracter,dict_key, button, loop_soup ) for button in downloadbutton]
	        
                                                                                                                               
def tab_distribute(downloadbutton,  link_types):
	print(f"scraping {link_types} Links.....")
	
	with concurrent.futures.ThreadPoolExecutor() as executor:
	    for button in downloadbutton:
	    	if button.text == "Patches": pass
	    	else:
	    		dict_key = button.text.strip()
	    		data_dict[dict_key] = []
	    		executor.submit(looper, dict_key, str(button))
	
	main_dict[link_types] = copy.deepcopy(data_dict)
	data_dict.clear()   


			
def WEBPAGE_GRABBER(url: str):
	global post_id
	
	try: website_html = client.get(url).text
	except: print("please enter the correct episode link."); sys.exit()
	
	try:
		post_id = POST_ID_REGEX.search(website_html).group(0).split(":")[1].split('"')[1]
		payload_data_matches = DDL_REGEX.finditer(website_html)
	except: print("Something Went wrong :(")
	
	
	for match in payload_data_matches:   
		payload = DDL_DECRYPTER(match)
		del payload["num"]     
		
		link_types = "DDL" if payload["tab_id"] == "2" else "WORKER" if payload["tab_id"] == "4" else "GDRIVE"
		
		response = client.post("https://animekaizoku.com/wp-admin/admin-ajax.php",headers=headers, data=payload)
		soup = BeautifulSoup(response.text, "html.parser")  
		
		downloadbutton = soup.find_all(class_="downloadbutton")
		tab_distribute(downloadbutton, link_types)
		
	dictionary_decrypter()
			  
  		  
    		  
if __name__ == "__main__":
	WEBPAGE_GRABBER(input("Enter the anime link wich you want to scrape from animekaizoku.com (ex: https://animekaizoku.com/aoashi-49052/):  "))
	
	
	
