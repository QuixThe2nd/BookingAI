import speech_recognition as sr
import os
import openai
import shlex
import requests
from time import sleep
import vonage

messages = [
    {"role": "system", "content": "I want you to act as an assistant. Your job is to find the perfect place to eat for your client. Ask them questions till you know what category is best. Keep your messages under 2 sentences. Once you know what category to recommend, just say \"done\" exactly, dont add anything else. Do not actually recommend anywhere."}
]

google_api_key = 'xxxxx'
openai.api_key = 'xxxxxx'
vonage_application_id = "xxxxxx"


def say(text):
    os.system("say " + shlex.quote(text))


def generate_response(messages):
    tmp_messages = messages
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=tmp_messages
        )
        return response.choices[0].message
    except Exception as e:
        print(e)
        return "I'm sorry, I don't understand."


def get_user_input(prompt='User:'):
    try:
        recogniser = sr.Recognizer()
        with sr.Microphone() as source:
            print("Say Something...")
            audio = recogniser.listen(source, timeout=5)
            print('Done Listening')
    except:
        return input(prompt + ' ')
    try:
        print('Processing...')
        user_input = recogniser.recognize_google(audio)
        print(prompt + ' ' + user_input)
        return user_input
    except sr.UnknownValueError:
        print("Speech recognition could not understand audio.")
        return input(prompt + ' ')
    except sr.RequestError as e:
        print("Could not request results from Speech Recognition service: {}".format(e))
        return input(prompt + ' ')
    except:
        return input(prompt + ' ')


while True:
    user_input = get_user_input()
    messages.append({"role": "user", "content": user_input})
    bot_response = generate_response(messages)
    if bot_response['content'].lower() == 'done' or bot_response['content'].lower() == 'done.' or bot_response['content'].lower() == 'done!':
        break
    print("Bot:", bot_response["content"])
    say(bot_response["content"])
    messages.append({"role": "assistant", "content": bot_response["content"]})

messages.append({"role": "system", "content": "Output one exact query to search on google to find restaurunts in that category. dont add anything else, dont add any placeholders like [location]"})
query = generate_response(messages)['content']
print(query)
location = f"-10.1234,90.4321"
radius = "10000"

response = requests.request("GET", "https://maps.googleapis.com/maps/api/place/textsearch/json", params={'query': query, 'location': location, 'radius': radius, 'key': google_api_key, 'type': 'restaurant'})

restaurant = None
restaurants = response.json()['results']
for restaurant in restaurants:
    say(restaurant['name'] + ' has a ' + str(restaurant['rating']) + ' star rating')
    print("\nOption " + str(restaurants.index(restaurant) + 1) + ":")
    print("\033[94m" + restaurant["name"] + "\033[0m")
    print("Address:", restaurant["formatted_address"])
    print("Rating:", restaurant["rating"])
    if "price_level" in restaurant:
        print("Price Level:", restaurant["price_level"])
    print("Open Now:", restaurant["opening_hours"]["open_now"])
    selection = get_user_input('Do you want this one?')
    if 'yes' in selection.lower() or 'yeah' in selection.lower() or 'yep' in selection.lower() or 'yup' in selection.lower():
        break
    sleep(1)

say(restaurant['name'] + ' is a great choice!')

phone_number = requests.request("GET", "https://maps.googleapis.com/maps/api/place/details/json", params={'place_id': restaurant['place_id'], 'key': google_api_key}).json()["result"]
if 'international_phone_number' in phone_number:
    phone_number = phone_number['international_phone_number']
else:
    phone_number = ''
print("The phone number is:", phone_number)


say('What day and time would you like to make the reservation for?')
time = get_user_input('What day and time would you like to make the reservation for? ')
say('How many people will be in your party?')
people = get_user_input('How many people will be in your party? ')
say('What name should the reservation be under?')
name = get_user_input('What name should the reservation be under? ')
say('What phone number should the reservation be under?')
phone = get_user_input('What phone number should the reservation be under? ')

say('I will now call the restaurant to make the reservation. I will call you back when I am done.')

messages = [
    {"role": "system", "content": f"I want you to act as an assistant. You are talking to a waiter at a {restaurant['name']} over the phone. You are to make a reservation for a client."},
    {"role": "system", "content": f"The client is looking to make a reservation for {people} people on {time}. The reservation should be under the name {name} and the phone number {phone}."}
]


while True:
    user_input = get_user_input('Waiter:')
    if 'bye' in user_input.lower() or ' by ' in user_input.lower():
        break
    messages.append({"role": "user", "content": user_input})
    bot_response = generate_response(messages)
    print("Bot:", bot_response["content"])
    say(bot_response["content"])
    messages.append({"role": "assistant", "content": bot_response["content"]})

client = vonage.Client(
    application_id=vonage_application_id,
    private_key='/path/to/private.key'
)


voice = vonage.Voice(client)

response = voice.create_call({
    'to': [{'type': 'phone', 'number': "xxxxxxxxxx"}],
    'from': {'type': 'phone', 'number': "xxxxxxxxxx"},
    'ncco': [
        {'action': 'input'},
        {'action': 'talk', 'text': 'Hello, just calling to let you know the reservation has been made at the time you requested.'}
    ]
})
print(response)
