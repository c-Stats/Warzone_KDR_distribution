################################################
############# LIBS #############################
################################################

from selenium import webdriver
from selenium.webdriver import ActionChains

import multiprocessing
import concurrent.futures

from tqdm import tqdm

import requests
import urllib

import pandas as pd
import numpy as np

################################################


################################################
############# PARAMETERS #######################
################################################

#Use your own path
webdriver_path = "D:/MLB/MLB_Modeling/chromedriver"

#Use your own player url
urls = ["https://cod.tracker.gg/warzone/profile/battlenet/FrankFredj%231458/matches",
		"https://cod.tracker.gg/warzone/profile/atvi/Huskerrs/overview",
		"https://cod.tracker.gg/warzone/profile/xbl/SwaggXBL/overview"]

driver = webdriver.Chrome(webdriver_path)

################################################


################################################
############# LOGIN      #######################
################################################

#Anti-robot captcha
# ----- Manually log in on the website after runnning this line -----
driver.get(urls[0])
# -------------------------------------------------------------------


################################################



################################################
############# FUNCTIONS     ####################
################################################


#Default sample size is 250. If you want to sample more/less, then tweak the function below. (i.e.: sample_size = 450)


def scrape_match_links(driver, url, sample_size = 250):

	driver.get(url)

	#Load more matches...
	n_sampled = 0
	n_ticks = 0

	while n_sampled < sample_size and n_ticks < 7:

		try:

			n_ticks = 0

			buttons = driver.find_elements_by_class_name("trn-button")
			load_more_button = load_more_button = [b for b in buttons if b.text in ["Load More Matches", "View All Matches"]]

			if len(load_more_button) == 0:
				n_ticks += 1
				continue

			ActionChains(driver).click(load_more_button[0]).perform()

			n_sampled = len(driver.find_elements_by_class_name("match-row__link"))

		except:

			continue


	match_links = [x.get_attribute("href") for x in driver.find_elements_by_class_name("match-row__link")]

	return match_links



def extract_stats(driver, url):

	driver.get(url)
	stats = driver.find_elements_by_class_name("stats")
	while len(stats) == 0:
		stats = driver.find_elements_by_class_name("stats")

	stats = [x.text for x in stats]

	game_type = driver.find_element_by_class_name("title").text
	if game_type == "BR Solos":

		stats = [x for x in stats if not "K/D" in x and not "Kills" in x]
		stats = [x for x in stats if "#" in x]
		kdrs = [float(x.split("\n")[0]) for x in stats]

	else:

		stats = [x for x in stats if "K/D" in x]
		kdrs = [float(x.split("\n")[1]) for x in stats]

	if "Quads" in game_type:
		del kdrs[0:4]
	elif "Trios" in game_type:
		del kdrs[0:3]
	elif "Duos" in game_type:
		del kdrs[0:2]
	else:
		del kdrs[0]

	game_info = driver.find_element_by_class_name("info").text

	game_date = game_info.split(",")[0]
	game_time = game_info.split(",")[-1].split("\n")[0].strip()

	output = pd.DataFrame(kdrs)
	output.columns = ["KDR"]
	output["Date"] = game_date
	output["Time"] = game_time
	output["Mode"] = game_type

	return output



def extract_stats_vectorized(driver, urls):

	kdrs = []

	n = len(urls)
	counter = 0
	for x in tqdm(urls):

		counter += 1

		try:

			kdrs.append(extract_stats(driver, x))

		except:

			continue

		if counter % 10 == 0:

			sample_size = np.sum([len(x) for x in kdrs])
			print("Sample size:" + str(sample_size))

	return pd.concat(kdrs, 0).reset_index(drop = True)


################################################


################################################
############# SCRAPE        ####################
################################################


#Get matches urls
matches = [scrape_match_links(driver, url) for url in urls]
kdrs = [extract_stats_vectorized(driver, match_urls) for match_urls in matches]

################################################


################################################
############# SAVE          ####################
################################################

#These names are used to name the files that will be saved. They should correspond to the variable "urls" declared at the top of the file.
names = ["FrankFredj%231458", "Huskerrs", "SwaggXBL"]

for frame, name in zip(kdrs, names):
	frame.to_csv("D:/CoD_data/" + name + ".csv")
	
################################################

