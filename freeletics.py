import requests
import json
import datetime
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import math
from getpass import getpass
from operator import itemgetter
from collections import OrderedDict
import os

# Function to get credentials
def get_credentials():
	i_user = input("Please enter your freeletics mailaddress: ")
	i_pass = getpass("Please enter your freeletics password: ")
	i_user = "toflpu@gmail.com"
	i_pass = "topu100285"
	return {"login": {"email":i_user,"password":i_pass}}

# Function to get the period 
def getDates():
	date_start_i = input("Please enter start date in format '2018/10/25': ")
	date_end_i = input("Please enter end date in format '2018/10/25': ")
	date_start = datetime.datetime.strptime(date_start_i, '%Y/%m/%d')
	date_end = datetime.datetime.strptime(date_end_i, '%Y/%m/%d')
	return [date_start,date_end]

# Function to change the image size
def changeImageSize(maxWidth,maxHeight,image):
    
    widthRatio  = maxWidth/image.size[0]
    heightRatio = maxHeight/image.size[1]

    newWidth    = int(widthRatio*image.size[0])
    newHeight   = int(heightRatio*image.size[1])

    newImage    = image.resize((newWidth, newHeight))
    return newImage

# Function to get centered text coordinates
def getCenteredCoordinates(img,text,centerLine,font):
	draw = ImageDraw.Draw(img)
	w, h = draw.textsize(text,font=font)
	return centerLine-w/2

# Function to get centered text coordinates
def getRightAlignedCoordinates(img,text,rightLine,font):
	draw = ImageDraw.Draw(img)
	w, h = draw.textsize(text,font=font)
	return rightLine-w

# Function to Login and return Bearer token
def getLoginBearer(login_payload):
	url_login = 'https://api.freeletics.com/user/v1/auth/password/login'
	login_response = requests.post(url_login, json=login_payload)
	login_ans = json.loads(login_response.text)
	return login_ans["auth"]["id_token"]

# Function to create Header with valid Bearer token
def getCreateHeader(id_token):
	return {'Authorization': 'Bearer '+id_token}

# Function to get feed pages
def getFeed(feed_page,header):
	url_feed = 'https://api.freeletics.com/v3/users/4155941/feed_entries?page='
	return requests.get(url_feed+feed_page, headers=header).text

# Function to create a feed dict containing only workouts within entered period (dates)
def getCreateFeedDict(dates,header):
	i=1
	exit_flag = False
	workout_entries = []
	while len(getFeed(str(i),header)):
		feed_page = json.loads(getFeed(str(i),header))
		for workout in feed_page["feed_entries"]:
			date = datetime.datetime.strptime(workout["created_at"][0:10], '%Y-%m-%d')
			if date >= dates[0] and date <= dates[1]:
				workout_entries.append(workout)
			else:
				if date < dates[0]:
					exit_flag = True
					break
		i = i + 1
		if exit_flag:
			break
	feed = {"workout_entries":workout_entries}
	return feed

# Function to retrieve photo url from feed dict
def getFotoUrl(feed):
	return feed["workout_entries"][0]["user"]["profile_pictures"]["max"]

# Function to count workouts in feed dict
def getWorkoutsCount(feed):
	workout_list = {}
	for entry in feed["workout_entries"]:
		if entry["object"]["workout"]["full_title"] in workout_list:
			workout_list.update({entry["object"]["workout"]["full_title"]: workout_list[entry["object"]["workout"]["full_title"]] + 1})
		else:
			workout_list.update({entry["object"]["workout"]["full_title"]: 1})
	return workout_list

# Function to count exercises in feed dict
def getExercisesCount(feed):
	exercise_list = {}
	for entry in feed["workout_entries"]:
		for round in entry["object"]["workout"]["rounds"]:
				for exercise in round:
					if "exercise_slug" in exercise and isinstance(exercise["quantity"], int):
						if exercise["exercise_slug"] in exercise_list:
							if exercise["exercise_slug"] == "run":
								exercise_list.update({exercise["exercise_slug"]: exercise_list[exercise["exercise_slug"]] + exercise["quantity"]})
							elif exercise["exercise_slug"] == "rest":
								exercise_list.update({exercise["exercise_slug"]: exercise_list[exercise["exercise_slug"]] + math.floor(exercise["quantity"]/60)})
							else:
								exercise_list.update({exercise["exercise_slug"]: exercise_list[exercise["exercise_slug"]] + exercise["quantity"]})
						else:
							if exercise["exercise_slug"] == "run":
								exercise_list.update({exercise["exercise_slug"]: math.floor(exercise["quantity"]/1000)})
							elif exercise["exercise_slug"] == "rest":
								exercise_list.update({exercise["exercise_slug"]: math.floor(exercise["quantity"]/60)})
							else:
								exercise_list.update({exercise["exercise_slug"]: exercise["quantity"]})	
		if entry["object"]["workout"]["base_name"] == "free-run":
			if "run" in exercise_list:
				exercise_list.update({"run": exercise_list["run"] + entry["object"]["distance"]})
			else:
				exercise_list.update({"run": entry["object"]["distance"]})
	return exercise_list

# Function to get which exercises should be printed on photo (user input). returns dict.
def getExercisesForPrint(sortedExercise_list,sortedWorkout_list):
	completeList = {**sortedWorkout_list, **sortedExercise_list}
	print("##################################")
	print("List of Exercises to choose from:")
	for keys,values in completeList.items():
		print(keys,":",values)
	
	print("##################################")
	print("Please enter 4 workouts or exercises you want to have printed on the picture.")
	exercisesForPrint = input("Enter comma-delimeted, e.g. burpees,situps,squat,DIONE: ").split(",")
	exercisesForPrintFinal = {}
	for exercise in exercisesForPrint:
		if exercise == "run":
			exercisesForPrintFinal.update({exercise:str(math.floor(completeList[exercise]/1000))+"k"})
		else:
			exercisesForPrintFinal.update({exercise:completeList[exercise]})

	return exercisesForPrintFinal

# Function to get username from feed dict
def getUsername(feed):
	return feed["workout_entries"][0]["user"]["first_name"] + " " + feed["workout_entries"][0]["user"]["last_name"]

# Function to create base image including profile picture with grey layer and freeletics logo
def doCreateBaseImage(feed):

	photo_url = getFotoUrl(feed)
	if photo_url is None or photo_url == "" or photo_url == "Null":
		img = Image.open(os.path.dirname(os.path.abspath(__file__))+"/background.png")
	else:
		response = requests.get(photo_url)
		img = Image.open(BytesIO(response.content))
	
	img_layer = Image.open(os.path.dirname(os.path.abspath(__file__))+"/grey.png")
	img_logo = Image.open(os.path.dirname(os.path.abspath(__file__))+"/logo1.png")
	#img_medal = Image.open("/Users/topu/Desktop/medal.png")

	width, height = img.size
	img_layer = changeImageSize(width, height, img_layer)
	img = img.convert("RGBA")
	img_layer = img_layer.convert("RGBA")
	img = Image.blend(img, img_layer, alpha=.7)
	img.paste(img_logo,(950,50), mask=img_logo)

	return img

# Function for printing selected exercises on image including blue lines
def doPrintExercises(img,exercisesForPrintList):
	font_count = ImageFont.truetype(os.path.dirname(os.path.abspath(__file__))+"/sansblack.otf", size=55)
	font_text = ImageFont.truetype(os.path.dirname(os.path.abspath(__file__))+"/sansblack.otf", size=28)
	x = 295
	y = 150
	counter= 0
	draw = ImageDraw.Draw(img)
	draw.line((x-175,y+120, x+175, y+120), fill='rgb(0, 74, 255)', width=3)
	draw.line((x+355,y+120, x+705, y+120), fill='rgb(0, 74, 255)', width=3)
	for key, value in exercisesForPrintList.items():
		draw.text((getCenteredCoordinates(img,str(value),x,font_count), y), str(value),fill='rgb(255, 255, 255)',font=font_count) #550
		draw.text((getCenteredCoordinates(img,str(key),x,font_text), y+60), str(key),fill='rgb(255, 255, 255)',font=font_text) #610
		counter=counter+1
		if counter == 1:
			x=x+530 #825			
		if counter == 2:
			x=x-530 #295
			y=y+115 #265
		if counter == 3:
			x=x+530 #825

	return img

# Function to get stats form feed dict
def getStats(feed,exercise_list):
	stats = {}
	pb_count = 0
	days_trained_on = 0
	seconds = 0
	repetitions = 0
	date_old = datetime.datetime(1970, 1, 1)
	for entry in feed["workout_entries"]:
		if entry["object"]["personal_best"] == True:
			pb_count = pb_count + 1
		date = datetime.datetime.strptime(entry["created_at"][0:10], '%Y-%m-%d')
		if date != date_old:
			days_trained_on = days_trained_on + 1
			date_old = date
		seconds = seconds + entry["object"]["seconds"]

		repetitions = sum(exercise_list.values())

		if "run" in exercise_list:
			repetitions = repetitions-exercise_list["run"]+math.floor(exercise_list["run"]/1000)
		if "rest" in exercise_list:
			repetitions = repetitions-exercise_list["rest"]

	return {"minutes":str(math.ceil(seconds/60)),"days":str(days_trained_on),"pb":str(pb_count),"reps":str(repetitions)}

# Function to print stats on image including blue lines and icons
def doPrintStats(img,stats):

	draw = ImageDraw.Draw(img)
	font_count = ImageFont.truetype(os.path.dirname(os.path.abspath(__file__))+"/sansblack.otf", size=55)
	font_text = ImageFont.truetype(os.path.dirname(os.path.abspath(__file__))+"/sansblack.otf", size=28)

	img_stopwatch = Image.open(os.path.dirname(os.path.abspath(__file__))+"/stopwatch.png")
	img_exercise = Image.open(os.path.dirname(os.path.abspath(__file__))+"/exercise2.png")
	img_exercise = img_exercise.convert("RGBA")
	img_pb = Image.open(os.path.dirname(os.path.abspath(__file__))+"/pb.png")
	img_reps = Image.open(os.path.dirname(os.path.abspath(__file__))+"/reps.png")

	x = 560
	y = 820

	draw.line((x-440,y, x-90, y), fill='rgb(0, 74, 255)', width=3) #500
	draw.line((x+90,y, x+460, y), fill='rgb(0, 74, 255)', width=3) #500

	img.paste(img_stopwatch,(x-410,y-100), mask=img_stopwatch) #400
	draw.text((x-320, y-120), stats["minutes"],fill='rgb(255, 255, 255)',font=font_count) #380
	draw.text((x-320, y-60), 'minutes trained',fill='rgb(255, 255, 255)',font=font_text) #440
	
	img.paste(img_exercise,(x+345,y-100), mask=img_exercise) #400
	draw.text((getRightAlignedCoordinates(img,stats["days"],x+320,font_count), y-120), stats["days"],fill='rgb(255, 255, 255)',font=font_count) #380
	draw.text((getRightAlignedCoordinates(img,'days trained on',x+320,font_text), y-60), 'days trained on',fill='rgb(255, 255, 255)',font=font_text) #440
	
	img.paste(img_pb,(x-410,y+15), mask=img_pb) #400
	draw.text((x-320, y-5), stats["pb"],fill='rgb(255, 255, 255)',font=font_count) #380
	draw.text((x-320, y+55), 'personal bests',fill='rgb(255, 255, 255)',font=font_text) #440
	
	img.paste(img_reps,(x+345,y+15), mask=img_reps) #400
	draw.text((getRightAlignedCoordinates(img,stats["reps"],x+320,font_count), y-5), stats["reps"],fill='rgb(255, 255, 255)',font=font_count) #380
	draw.text((getRightAlignedCoordinates(img,'repetitions',x+320,font_text), y+55), 'repetitions',fill='rgb(255, 255, 255)',font=font_text) #440

	return img

# Function to get slogan (user input) line1 and line2 (max. 25 chars each line)
def getSlogan():
	line1_ok = False
	line2_ok = False
	while not line1_ok:
		line1 = input("Please enter text for first line (max. 25 characters): ").upper()
		if len(line1)<25:
			line1_ok = True
		else:
			print("First line has more than 25 characters. Please try again.")

	while not line2_ok:
		line2 = input("Please enter text for second line (max. 25 characters): ").upper()
		if len(line2)<25:
			line2_ok = True
		else:
			print("Second line has more than 25 characters. Please try again.")

	if len(line1)==0 and len(line2)==0:
		line1 = "IN 2019 I ACHIEVED"
		line2 = "MORE WITH FREELETICS"
	return [line1,line2]

# Function to print slogan on images including blue box
def doPrintSlogan(img,slogan):
	draw = ImageDraw.Draw(img)
	font_slogan = ImageFont.truetype(os.path.dirname(os.path.abspath(__file__))+"/sansblack.otf", size=70)
	x=560
	y=440
	w, h = draw.textsize(slogan[1],font=font_slogan)
	draw.rectangle(((x-math.floor(w/2)-10, y+95), (x+math.ceil(w/2)+10, y+165)), fill='rgb(0, 74, 255)') #245,315
	draw.text((getCenteredCoordinates(img,slogan[0],x,font_slogan), y), slogan[0],fill='rgb(255, 255, 255)',font=font_slogan)
	draw.text((getCenteredCoordinates(img,slogan[1],x,font_slogan), y+70), slogan[1],fill='rgb(255, 255, 255)',font=font_slogan)
	
	
	
	return img

# Function to print username on image
def doPrintUsername(img,username):
	username_font = ImageFont.truetype(os.path.dirname(os.path.abspath(__file__))+"/sansblack.otf", size=28)
	draw = ImageDraw.Draw(img)
	draw.text((50, 54), username,fill='rgb(255, 255, 255)',font=username_font)
	return img

dates = getDates()
login_payload = get_credentials()
id_token = getLoginBearer(login_payload)
header = getCreateHeader(id_token)
feed = getCreateFeedDict(dates,header)

workout_list = getWorkoutsCount(feed)
exercise_list = getExercisesCount(feed)
sorted_workout_list = OrderedDict(sorted(workout_list.items(),key=itemgetter(1),reverse=True))
sorted_exercises_list = OrderedDict(sorted(exercise_list.items(),key=itemgetter(1),reverse=True))
exercisesForPrintList = getExercisesForPrint(sorted_workout_list,sorted_exercises_list)
username = getUsername(feed)

test_img = doCreateBaseImage(feed)
test_img = doPrintExercises(test_img,exercisesForPrintList)
stats = getStats(feed,exercise_list)
test_img = doPrintStats(test_img,stats)
slogan = getSlogan()
test_img = doPrintSlogan(test_img,slogan)
test_img = doPrintUsername(test_img,getUsername(feed))
test_img.show()

print("#####################################")


