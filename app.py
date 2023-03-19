import os
import openai
from flask import Flask, request, jsonify
from flask_cors import cross_origin
from flask import session


app = Flask(__name__)
app.secret_key = 'BAD_SECRET_KEY'

ALLOWED_EXTENSIONS = set(['mp3', 'wav'])
os.makedirs("uploaded_file", exist_ok = True)
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/file-upload', methods=['GET'])
def upload_file():
	# check if the post request has the file part
	if 'file' not in request.files:
		resp = jsonify({'message' : 'No file part in the request'})
		resp.status_code = 400
		return resp
	file = request.files['file']
	if file.filename == '':
		resp = jsonify({'message' : 'No file selected for uploading'})
		resp.status_code = 400
		return resp
	if file and allowed_file(file.filename):
		filename = "input.mp3"

		file.save(os.path.join("uploaded_file", filename))
		resp = jsonify({'message' : 'File successfully uploaded'})
		resp.status_code = 201
		return resp
	else:
		resp = jsonify({'message' : 'Allowed file types are mp3, wav'})
		resp.status_code = 400
		return resp

@app.route('/transcription', methods=['GET'])
@cross_origin()
def transcribe():
    try:
        api_token = request.json["api_key"]
        session['api_key'] = api_token
        openai.api_key = api_token
        files = os.listdir("uploaded_file")
        file = open(f"uploaded_file/{files[0]}", "rb")
        transcription = openai.Audio.translate("whisper-1", file)
        session['transcription'] = transcription['text']
        result = {"result": session['transcription']}
        return jsonify(result)
    except Exception as e: 
        return e.__str__()

@app.route('/summarize', methods=['GET'])
@cross_origin()
def summarize():
    try:
        api_token = session['api_key']
        openai.api_key = api_token
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", 
            messages=[{"role": "user", "content": f"Summarize the following conversation: {session['transcription']}"}]
        )

        content = completion["choices"][0]["message"]["content"]
        result = {"result": content}
        return jsonify(result)
    except Exception as e:
        return e.__str__()

@app.route('/ner', methods=['GET'])
@cross_origin()
def NER():
    try:
        api_token = session['api_key']
        # Prompt Engineering
        question = "Find the key entities with the entitie type using banking domain  from the followings text\n"
        training_data = "text:  Good morning Sir, this is Abhishek Mathur calling from Janta Bank. Am I speaking to Mr. Subhash Kapoor? Sir, I am Abhishek Mathur from Janta Bank. Ok, Ok, tell me Mr. Abhishek, what do you want? Sir, this is a general relationship call for your account. I hope you are happy with our service. Can I help you? Oh, thank you. You called me. I had a problem with my ATM card. I wanted to change my ATM. Can you help me? Sir, that is no problem. Do you have our app? Of course, I use it daily to check my account balance. In that case, please go to the service option in the app and there will be an option to change your ATM pin. There, please try it. Oh, thank you. You called me. I had a problem with my ATM card. I wanted to change my ATM. Can you help me? Sir, that is no problem. Do you have our app? Of course, I use it daily to check my account balance. In that case, please go to the service option in the app and there will be an option to change your ATM pin. There, please try it. Thank you.\n\nEntities:\nAbhishek Mathur : Bank Agent,\nMr. Subhash Kapoor : Bank Customer\nJanta Bank : Banking Institution\nATM card : Banking Product ATM\n\n"
        final_query = "text: "+ session['transcription']
        end = "\n\nEntities:\n"

        final_prompt = question+training_data+final_query+end

        openai.api_key = api_token
        response = openai.Completion.create(
        model="text-davinci-003",
        prompt=final_prompt,
        temperature=0.73,
        max_tokens=150,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
        )

        content = response["choices"][0]["text"].split("\n")
        result = {"result": content}
        return jsonify(result)

    except Exception as e:
        return e.__str__()

@app.route('/sentiment', methods=['GET'])
@cross_origin()
def sentriment_analysis():
    try:
        api_token = session['api_key']
        # Prompt Engineering
        question = "Generate the customer sentiment from the following test. Sentiment scale is Very Happy, Happy, Satisfied, Not Satisfied, Angry\n\n"
        end = "\n\nSentiment:\n"
        final_prompt = question+session['transcription']+end

        openai.api_key = api_token

        response = openai.Completion.create(
        model="text-davinci-003",
        prompt=final_prompt,
        temperature=0.7,
        max_tokens=100,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
        )
        content = response ["choices"][0]['text'].replace("\n", "")
        result = {"result": content}
        return jsonify(result)

    except Exception as e:
        return e.__str__()

@app.route('/product_count', methods=['GET'])
@cross_origin()
def product_count():
    try:
        api_token = session['api_key']
        # Prompt Engineering
        question = "Give number of times bank name and product name was mentioned in the following text:\n"
        final_prompt = question+session['transcription']

        openai.api_key = api_token

        response = openai.Completion.create(
        model="text-davinci-003",
        prompt=final_prompt,
        temperature=0.7,
        max_tokens=100,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
        )
        content = response ["choices"][0]['text'].lstrip("\n").split("\n")
        result = {"result": content}
        return jsonify(result)

    except Exception as e:
        return e.__str__()


if __name__ == "__main__":
    app.run(debug=True)