from flask import Flask, request
import requests
from twilio.twiml.messaging_response import MessagingResponse
import pandas as pd

app = Flask(__name__)

questions = ["Give me the top {input your digit} {goalkeepers/defenders/midfielders/forwards} that have an average form of more than {input a digit value} and cost {above/below} {input a digit value}"]
default_message = "Below are the questions I can answer for now:\n\n"+ questions[0]+\
                "\n\nPlease do not type in numbers in words, type using digits: 1, 2, 2.5, 6, 9.4 etc.\n"+\
                "\nAlso, I am automatically saving all your questions that don't exist now and then I'd make them available in the future"

@app.route('/fplbot', methods=['POST'])
def bot():
    url = 'https://fantasy.premierleague.com/api/bootstrap-static/'

    incoming_msg = request.values.get('Body', '').lower()
    resp = MessagingResponse()
    msg = resp.message()

    r =  requests.get(url)
    json = r.json()

    element_types = {}
    for et in json['element_types']:
        element_types[et['plural_name'].lower()] = et['id']

    elements_df = pd.DataFrame(json['elements'])
    elements_df['form'] = elements_df['form'].astype(float)

    #forms
    if 'form' in incoming_msg:
        try:
            digits = get_digits(incoming_msg)
            no_of_player_type, form, cost = digits
            element_type = element_types[get_element_type(incoming_msg)]
        except:
            save_question(incoming_msg)
            msg.body(default_message)
            return str(resp)

        if 'above' in incoming_msg:
            result = elements_df[(elements_df['form'] > float(form)) & (elements_df['now_cost']/10 > float(cost)) & (elements_df['element_type'] == element_type)]
        else:
            result = elements_df[(elements_df['form'] > float(form)) & (elements_df['now_cost']/10 < float(cost)) & (elements_df['element_type'] == element_type)]

        result.reset_index(inplace=True)
        result.sort_values(by=['form', 'now_cost'], ascending=[False, True], inplace=True)

        body = ""
        for number in range(int(no_of_player_type)):
            try:
                body += result['web_name'].iloc[number] + " has an average form of " + str(result['form'].iloc[number]) + " and costs $" + str(result["now_cost"].iloc[number]/10) + "m\n"
            except:
                continue
        msg.body(body)
    else:
        save_question(incoming_msg)
        msg.body(default_message)

    return str(resp)

def get_digits(incoming_msg):
    digits = []
    for number in incoming_msg.split(" "):
        try:
            digits.append(float(number))
        except:
            continue
    return digits

def get_element_type(incoming_msg):
    if 'midfielders' in incoming_msg:
        return 'midfielders'
    elif 'defenders' in incoming_msg:
        return 'defenders'
    elif 'forwards' in incoming_msg:
        return 'forwards'
    elif 'goalkeepers' in incoming_msg:
        return 'goalkeepers'

def save_question(incoming_msg):
    file = open("future_questions.txt", "a+")
    file.write(incoming_msg + "\n")
    file.close()