import requests
import json
import datetime
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import math


def get_credentials():
	i_user = input("Please enter your freeletics mailaddress: ")
	i_pass = input("Please enter your freeletics passwort: ")
	i_user = "toflpu@gmail.com"
	i_pass = "topu100285"
	return {"login": {"email":i_user,"password":i_pass}}



url_login = 'https://api.freeletics.com/user/v1/auth/password/login'
url_feed = 'https://api.freeletics.com/v3/users/4155941/feed_entries?page='

workout_count = {}
exercise_count = {}
repetitions_count = 0
i = 1
seconds = 0
count = 0
pb_count = 0
date_start = datetime.datetime(2019, 10, 30)
date_old = datetime.datetime(1970, 1, 1)
date_end = datetime.datetime(2019, 10, 31)
exit_flag = False


# Function to change the image size
def changeImageSize(maxWidth, 
                    maxHeight, 
                    image):
    
    widthRatio  = maxWidth/image.size[0]
    heightRatio = maxHeight/image.size[1]

    newWidth    = int(widthRatio*image.size[0])
    newHeight   = int(heightRatio*image.size[1])

    newImage    = image.resize((newWidth, newHeight))
    return newImage

# Function to get centered text coordinates
def getCenteredCoordinates(text,
						   centerLine,
						   font):
	w, h = draw.textsize(text,font=font)
	return centerLine-w/2

# Function to get centered text coordinates
def getRightAlignedCoordinates(text,
						   rightLine,
						   font):
	w, h = draw.textsize(text,font=font)
	return rightLine-w

def getLoginBearer(login_payload):
	url_login = 'https://api.freeletics.com/user/v1/auth/password/login'
	login_response = requests.post(url_login, json=login_payload)
	login_ans = json.loads(login_response.text)
	return login_ans["auth"]["id_token"]


def getCreateHeader(id_token):
	return {'Authorization': 'Bearer '+id_token}


def getFeed(feed_page,
			header):
	url_feed = 'https://api.freeletics.com/v3/users/4155941/feed_entries?page='
	return requests.get(url_feed+feed_page, headers=header).text

login_payload = get_credentials()
id_token = getLoginBearer(login_payload)
header = getCreateHeader(id_token)



#login_response = requests.post(url_login, json=login_payload)
#login_ans = json.loads(login_response.text)
#print(json.loads(login_response.text))
#id_token = login_ans["auth"]["id_token"]
#header = {'Authorization': 'Bearer '+id_token}


#while len(requests.get(url_feed+str(i), headers=header).text):
while len(getFeed(str(i),header)):
#while i < 2:
	feed_entries = requests.get(url_feed+str(i), headers=header)
	feed_ans = json.loads(feed_entries.text)
	for workout in feed_ans["feed_entries"]:
		date = datetime.datetime.strptime(workout["created_at"][0:10], '%Y-%m-%d')
		if date != date_old:
			count = count + 1
			date_old = date
		profil_picture = workout["user"]["profile_pictures"]["max"]
		username = workout["user"]["first_name"]+' '+workout["user"]["last_name"]
		seconds = seconds + workout["object"]["seconds"]
		if workout["object"]["personal_best"] == True:
			pb_count = pb_count + 1
		if date >= date_start and date <= date_end:
			print(date, ': ',workout["id"])	
			if workout["object"]["workout"]["full_title"] in workout_count:
				workout_count.update({workout["object"]["workout"]["full_title"]: workout_count[workout["object"]["workout"]["full_title"]] + 1})
			else:
				workout_count.update({workout["object"]["workout"]["full_title"]: 1})
			for round in workout["object"]["workout"]["rounds"]:
				for exercise in round:
					if "exercise_slug" in exercise and isinstance(exercise["quantity"], int):
						if exercise["exercise_slug"] in exercise_count:
							exercise_count.update({exercise["exercise_slug"]: exercise_count[exercise["exercise_slug"]] + exercise["quantity"]})
							if exercise["exercise_slug"] != "run" and exercise["exercise_slug"] != "rest":
								repetitions_count = repetitions_count + exercise["quantity"]
							if exercise["exercise_slug"] == "run":
								repetitions_count = repetitions_count + math.floor(exercise["quantity"]/1000)
						else:
							exercise_count.update({exercise["exercise_slug"]: exercise["quantity"]})
							if exercise["exercise_slug"] != "run" and exercise["exercise_slug"] != "rest":
								repetitions_count = repetitions_count + exercise["quantity"]
							if exercise["exercise_slug"] == "run":
								repetitions_count = repetitions_count + math.floor(exercise["quantity"]/1000)
		else:
			if date < date_start:
				exit_flag = True
				break   
	i = i + 1
	if exit_flag:
		break

for keys,values in workout_count.items():
    print(keys, ': ', values)

print('---------------')

for keys,values in exercise_count.items():
    print(keys, ': ', values)
minutes = str(math.ceil(seconds/60))
print(minutes,' Minuten trainiert')
print(username)
num_exercises = str(len(exercise_count.keys()))


#### Load Images ####
response = requests.get(profil_picture)
img = Image.open(BytesIO(response.content))
layer = Image.open("/Users/topu/Desktop/grey.png")
logo = Image.open("/Users/topu/Desktop/logo1.png")
medal = Image.open("/Users/topu/Desktop/medal.png")
pb = Image.open("/Users/topu/Desktop/pb.png")
stopwatch = Image.open("/Users/topu/Desktop/stopwatch.png")
exercise_img = Image.open("/Users/topu/Desktop/exercise2.png")
exercise_img = exercise_img.convert("RGBA")
reps = Image.open("/Users/topu/Desktop/reps.png")

#### LOAD FONTS ####
username_font = ImageFont.truetype('/Users/topu/Desktop/sansblack.otf', size=28)
font_slogan = ImageFont.truetype('/Users/topu/Desktop/sansblack.otf', size=70)
font_count = ImageFont.truetype('/Users/topu/Desktop/sansblack.otf', size=55)
font_text = ImageFont.truetype('/Users/topu/Desktop/sansblack.otf', size=28)
font_pb_count = ImageFont.truetype('/Users/topu/Desktop/sansblack.otf', size=70)
font_pb_text = ImageFont.truetype('/Users/topu/Desktop/sansblack.otf', size=28)
width, height = img.size
print(width,':',height)
layer = changeImageSize(width, height, layer)
img = img.convert("RGBA")
layer = layer.convert("RGBA")
final_img = Image.blend(img, layer, alpha=.7)
#final_img.paste(medal,(507,180), mask=medal) #600
final_img.paste(logo,(950,50), mask=logo)
#final_img.paste(pb,(505,910), mask=pb)



#### Create Image ####
# Draw Image Lines & Rectangle
draw = ImageDraw.Draw(final_img)
draw.line((120,820, 470, 820), fill='rgb(0, 74, 255)', width=3) #500
draw.line((650,820, 1000, 820), fill='rgb(0, 74, 255)', width=3) #500
draw.line((120,270, 470, 270), fill='rgb(0, 74, 255)', width=3) #670
draw.line((650,270, 1000, 270), fill='rgb(0, 74, 255)', width=3) #670
draw.rectangle(((195, 535), (920, 605)), fill='rgb(0, 74, 255)') #245,315

# Write Username
draw.text((50, 54), username,fill='rgb(255, 255, 255)',font=username_font)

# Write Title
draw.text((getCenteredCoordinates('IN 2019 I ACHIEVED',560,font_slogan), 440), 'IN 2019 I ACHIEVED',fill='rgb(255, 255, 255)',font=font_slogan)
draw.text((getCenteredCoordinates('MORE WITH FREELETICS',560,font_slogan), 510), 'MORE WITH FREELETICS',fill='rgb(255, 255, 255)',font=font_slogan)

# Write Time & Workout incl. Icons
final_img.paste(stopwatch,(150,720), mask=stopwatch) #400
draw.text((240, 700), minutes,fill='rgb(255, 255, 255)',font=font_count) #380
draw.text((240, 760), 'minutes trained',fill='rgb(255, 255, 255)',font=font_text) #440

final_img.paste(exercise_img,(905,720), mask=exercise_img) #400
#draw.text((getRightAlignedCoordinates(num_exercises,880,font_count), 700), num_exercises,fill='rgb(255, 255, 255)',font=font_count) #380
draw.text((getRightAlignedCoordinates(str(count),880,font_count), 700), str(count),fill='rgb(255, 255, 255)',font=font_count) #380
#draw.text((getRightAlignedCoordinates('exercises done',880,font_text), 760), 'exercises done',fill='rgb(255, 255, 255)',font=font_text) #440
draw.text((getRightAlignedCoordinates('days trained on',880,font_text), 760), 'days trained on',fill='rgb(255, 255, 255)',font=font_text) #440

final_img.paste(pb,(150,835), mask=pb) #400
draw.text((240, 815), str(pb_count),fill='rgb(255, 255, 255)',font=font_count) #380
draw.text((240, 875), 'personal bests',fill='rgb(255, 255, 255)',font=font_text) #440

final_img.paste(reps,(905,835), mask=reps) #400
draw.text((getRightAlignedCoordinates(str(repetitions_count),880,font_count), 815), str(repetitions_count),fill='rgb(255, 255, 255)',font=font_count) #380
draw.text((getRightAlignedCoordinates('repetitions',880,font_text), 875), 'repetitions',fill='rgb(255, 255, 255)',font=font_text) #440



# Write Exercises Count
# 1
draw.text((getCenteredCoordinates('2840',295,font_count), 150), '2840',fill='rgb(255, 255, 255)',font=font_count) #550
draw.text((getCenteredCoordinates('burpees',295,font_text), 210), 'burpees',fill='rgb(255, 255, 255)',font=font_text) #610
# 2
draw.text((getCenteredCoordinates('1225',825,font_count), 150), '1225',fill='rgb(255, 255, 255)',font=font_count) #550
draw.text((getCenteredCoordinates('climbers',825,font_text), 210), 'climbers',fill='rgb(255, 255, 255)',font=font_text) #610
# 3
draw.text((getCenteredCoordinates('1050',295,font_count), 265), '1050',fill='rgb(255, 255, 255)',font=font_count) #665
draw.text((getCenteredCoordinates('situps',295,font_text), 320), 'situps',fill='rgb(255, 255, 255)',font=font_text) #720
# 4
draw.text((getCenteredCoordinates('1500',825,font_count), 265), '1500',fill='rgb(255, 255, 255)',font=font_count) #665
draw.text((getCenteredCoordinates('squats',825,font_text), 320), 'squats',fill='rgb(255, 255, 255)',font=font_text) #720




#### Show Final Image ####
final_img.show()




