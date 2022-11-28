from flask import Flask, Response, request, jsonify

from aioflask import Flask, request, render_template, g, redirect, Response, session
from datetime import datetime
import json
from flask_cors import CORS
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from google.oauth2 import id_token
from pip._vendor import cachecontrol
import google.auth.transport.requests
import requests
import urllib
import json
import asyncio


# Create the Flask application object.
app = Flask(__name__, template_folder="templates")
# NEVER HARDCODE YOUR CONFIGURATION IN YOUR CODE
# TODO: INSTEAD CREATE A .env FILE AND STORE IN IT
app.config['SECRET_KEY'] = 'longer-secret-is-better'
CORS(app)

courseurl = "http://127.0.0.1:5011/course/"
coursepreference = "http://127.0.0.1:5011/course/student_preference/"
studenturl = "http://127.0.0.1:2333/students/"

async def get_profile(uni):
    with open("application.json") as json_file:
        json_decoded = json.load(json_file)[uni]
        try:
            profile = json_decoded["profile"]
        except:
            return False
    return profile

async def get_uni(uni):
    with open("application.json") as json_file:
        json_decoded = json.load(json_file)[uni]
        print(json_decoded)
        try:
            uni = json_decoded["uni"]
        except:
            return False
    return uni


@app.route("/course/", methods=["GET"])
def get_course_by_name(course_name = ""):
    if "course_name" in request.args:
        course_name = request.args["course_name"]
    rsp = requests.session().get(courseurl + '?course_name=' + course_name, verify=False)
    if rsp.status_code == 200:
        rsp = Response(json.dumps(rsp.json()), status=200, content_type="application.json")
    else:
        rsp = Response("NOT FOUND", status=404, content_type="text/plain")
    return rsp


@app.route("/course/add", methods=["POST"])
def insert_courses():
    if request.is_json:
        try:
            request_data = request.get_json()
        except ValueError:
            return Response("[COURSE] UNABLE TO RETRIEVE REQUEST", status=400, content_type="text/plain")
    else:
        return Response("[COURSE] INVALID POST FORMAT: SHOULD BE JSON", status=400, content_type="text/plain")
    if not request_data:
        rsp = Response("[COURSE] INVALID INPUT", status=404, content_type="text/plain")
        return rsp

    course_name, department, introduction = request_data['course_name'], request_data['department'], request_data[
        'introduction']
    rsp = requests.session().post(courseurl + 'add', verify=False,
                                  json={'course_name':course_name, 'department':department, 'introduction':introduction})
    if rsp.status_code == 200:
        rsp = Response("COURSE CREATED", status=200, content_type="text/plain")
    else:
        rsp = Response("There already exist one course", status=404, content_type="text/plain")
    return rsp

@app.route("/course/student_preference/add",methods=["POST"])
async def add_course_preference():
    if request.is_json:
        try:
            request_data = request.get_json()
        except ValueError:
            return Response("[COURSE] UNABLE TO RETRIEVE REQUEST", status=400, content_type="text/plain")
    else:
        return Response("[COURSE] INVALID POST FORMAT: SHOULD BE JSON", status=400, content_type="text/plain")
    if not request_data:
        rsp = Response("[COURSE] INVALID INPUT", status=404, content_type="text/plain")
        return rsp
    uni, course_id, timezone, dept, message = request_data['uni'], request_data['course_id'], request_data['timezone'], \
                                              request_data['Dept'], request_data['message']
    ##Make Sure user must edit profile and log in before other operations
    loop = asyncio.get_event_loop()
    t1 = loop.create_task(get_profile(uni))
    t2 = loop.create_task(get_uni(uni))
    profile, uni = await asyncio.gather(t1, t2)
    if not uni or not profile:
        return Response("You have not logged in or not edited profile", status=404, content_type="text/plain")
    rsp = requests.session().post(coursepreference + 'add', verify=False,
        json={'uni':uni, 'course_id':course_id, 'timezone':timezone, 'Dept':dept, 'message':message })
    if rsp.status_code == 200:
        rsp = Response("Course Preferences CREATED", status=200, content_type="text/plain")
    else:
        rsp = Response(rsp.text, status=404, content_type="text/plain")
    return rsp

@app.route("/course/student_preference/", methods=["GET"])
async def get_course_preference_by_uni(uni = "", limit = "", offset = ""):
    if "uni" in request.args and "limit" in request.args and "offset" in request.args:
        uni, limit, offset = request.args["uni"], request.args["limit"], request.args["offset"]
    ##Make Sure user must edit profile and log in before other operations
    loop = asyncio.get_event_loop()
    t1 = loop.create_task(get_profile(uni))
    t2 = loop.create_task(get_uni(uni))
    profile, uni = await asyncio.gather(t1, t2)
    print(uni)
    print(profile)
    if not uni or not profile:
        return Response("You have not logged in or not edited profile", status=404, content_type="text/plain")
    rsp = requests.session().get(coursepreference + '?uni=' + uni +'&limit=' + limit + '&offset=' + offset, verify=False)
    if rsp.status_code == 200:
        rsp = Response(json.dumps(rsp.json()), status=200, content_type="application.json")
    else:
        rsp = Response("NOT FOUND", status=404, content_type="text/plain")
    return rsp

@app.route("/course/student_preference/edit/", methods=["GET", "POST"])
def edit_course_preference():
    if request.is_json:
        try:
            request_data = request.get_json()
        except ValueError:
            return Response("[COURSE] UNABLE TO RETRIEVE REQUEST", status=400, content_type="text/plain")
    else:
        return Response("[COURSE] INVALID POST FORMAT: SHOULD BE JSON", status=400, content_type="text/plain")
    if not request_data:
        rsp = Response("[COURSE] INVALID INPUT", status=404, content_type="text/plain")
        return rsp
    uni, course_id, timezone, dept, messages = request_data['uni'], request_data['course_id'], request_data['timezone'], request_data['Dept'], request_data['message']
    rsp = requests.session().post(coursepreference + 'edit', verify=False,
        json={'uni':uni, 'course_id':course_id, 'timezone':timezone, 'Dept':dept, 'message':messages })
    if rsp.status_code == 200:
        rsp = Response("Course Preferences CREATED", status=200, content_type="text/plain")
    else:
        rsp = Response("The preference does not exist", status=404, content_type="text/plain")
    return rsp


@app.route("/course/student_preference/delete/",methods=["POST", "GET"])
def delete_course_preference_by_id_and_uni():
    if request.is_json:
        try:
            request_data = request.get_json()
        except ValueError:
            return Response("[COURSE] UNABLE TO RETRIEVE REQUEST", status=400, content_type="text/plain")
    else:
        return Response("[COURSE] INVALID POST FORMAT: SHOULD BE JSON", status=400, content_type="text/plain")
    if not request_data:
        rsp = Response("[COURSE] INVALID INPUT", status=404, content_type="text/plain")
        return rsp
    uni, course_id = request_data['uni'], request_data['course_id']
    rsp = requests.session().post(coursepreference + 'delete', verify=False, json={'uni':uni, 'course_id':course_id})
    if rsp.status_code == 200:
        rsp = Response("DELETE SUCCESS", status=200, content_type="application.json")
    else:
        rsp = Response("No existed Preference is found!", status=404, content_type="text/plain")
    return rsp

@app.route("/students/login", methods=['POST'])
def login():
    request_data = request.get_json()
    uni, password = request_data['uni'], request_data['password']
    rsp = requests.session().post(studenturl + 'login', verify=False, json={'uni': uni, 'password': password})
    if rsp.status_code == 200:
        rsp_json = rsp.json()
        rsp = Response(json.dumps(rsp.json()), status=200, content_type="text/plain")
        try:
            with open("application.json") as json_file:
                json_decoded = json.load(json_file)
            json_decoded[uni] = {"uni": uni}
            with open("application.json", 'w') as json_file:
                json.dump(json_decoded, json_file)
        except:
            json_decoded = {}
            json_decoded[uni] = {"uni": uni}
            with open("application.json", 'w') as json_file:
                json.dump(json_decoded, json_file)
    else:
        rsp = Response(rsp.text, status=rsp.status_code, content_type="text/plain")
    return rsp


@app.route("/students/account", methods=["POST"])
def update_account_info():
    request_data = request.get_json()
    uni, password = request_data['uni'], request_data['password']
    rsp = requests.session().post(studenturl + 'account', verify=False, json={'uni': uni, 'password': password}, headers = request.headers)
    rsp = Response(rsp.text, status=rsp.status_code, content_type="text/plain")
    return rsp

@app.route("/students/loginwithgoogle", methods=['GET', 'POST'])
def login_with_google():
    request_data = request.get_json()
    rsp = requests.session().post(studenturl + 'loginwithgoogle', verify=False, json = request_data)
    if rsp.status_code == 200:
        rsp_json = rsp.json()
        rsp = Response(json.dumps(rsp.json()), status=200, content_type="text/plain")
        email = rsp_json["email"]
        uni = email[:email.index('@')]
        try:
            with open("application.json") as json_file:
                json_decoded = json.load(json_file)
            json_decoded[uni] = {"uni": uni}
            with open("application.json", 'w') as json_file:
                json.dump(json_decoded, json_file)
        except:
            json_decoded = {}
            json_decoded[uni] = {"uni": uni}
            with open("application.json", 'w') as json_file:
                json.dump(json_decoded, json_file)
    else:
        rsp = Response(rsp.text, status=rsp.status_code, content_type="text/plain")

    return rsp

@app.route("/students/signup", methods=['POST'])
def signup():
    request_data = request.get_json()
    rsp = requests.session().post(studenturl + 'signup', verify=False, json=request_data)
    rsp = Response(rsp.text, status=rsp.status_code, content_type="text/plain")
    return rsp

@app.route("/students/account", methods=["GET"])
def get_student_by_input(uni="", email=""):
    if "uni" in request.args:
        uni = request.args["uni"]
    if "email" in request.args:
        email = request.args["email"]
    if uni != "" and email != "":
        rsp = requests.session().get(studenturl + 'account' + '?uni=' + uni + '&email=' + email, verify=False, headers = request.headers)
    elif uni != "":
        rsp = requests.session().get(studenturl + 'account' + '?uni=' + uni, verify=False, headers = request.headers)
    else:
        rsp = requests.session().get(studenturl + 'account' + '?email=' + email, verify=False, headers = request.headers)
    if rsp.status_code == 200:
        rsp = Response(json.dumps(rsp.json()), status=200, content_type="application.json")
    else:
        rsp = Response("NOT FOUND", status=401, content_type="text/plain")
    return rsp


@app.route("/students/profile", methods=["GET"])
def get_profile_by_uni():
    rsp = requests.session().get(studenturl + 'profile', verify=False, headers = request.headers)
    if rsp.status_code == 404:
        return rsp.text
    else:
        rsp_json = rsp.json()
        uni = rsp_json["uni"]
        del rsp_json['uni']
        ###Add profile in the application.json file
        with open("application.json") as json_file:
            json_decoded = json.load(json_file)
        json_decoded[uni]["profile"] = rsp_json
        with open("application.json", 'w') as json_file:
            json.dump(json_decoded, json_file)
        return Response(json.dumps(rsp.json()), status=200, content_type="application.json")

@app.route("/students/profile", methods=["POST"])
def update_profile():
    request_data = request.get_json()
    rsp = requests.session().post(studenturl + 'profile', verify=False, json=request_data, headers = request.headers)
    rsp = Response(rsp.text, status=rsp.status_code, content_type="text/plain")
    return rsp

@app.route("/students/resend", methods=["POST"])
def resend_confirmation():
    request_data = request.get_json()
    rsp = requests.session().post(studenturl + 'resend', verify=False, json=request_data)
    return rsp.text

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=1000)
    # app.run(ssl_context="adhoc")