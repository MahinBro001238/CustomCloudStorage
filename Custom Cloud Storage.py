from flask import Flask, request, session, redirect, send_file, jsonify
import os
import time
import smtplib
from datetime import datetime
import shutil
import ssl
import random
from pathlib import Path
import json
from natsort import natsorted
from hashlib import sha256
from threading import Thread
import base64
from email.message import EmailMessage
account_not_found = """<!DOCTYPE html>
<html>
    <head>
        <title>Custom Cloud Storage</title>
    </head>
    <body style="font-family: Arial; margin: 0; background-color: #f5f6fa">
        <header style="font-size: 24px; background-color: #1f2937; color: white; font-weight: bold; padding: 16px 32px">Custom Cloud Storage</header>
        <div style="height: calc(100vh - 60px); display: flex; justify-content: center; align-items: center">
            <div style="border-radius: 8px; background-color: white; padding: 30px; width: 400px; display: flex; align-items: center; justify-content: center; flex-direction: column; box-shadow: -4px 4px 10px rgba(0, 0, 0, 0.1)">
                <h2 style="margin-bottom: 20px">Account not found</h2>
                <p style="text-align: center; margin-bottom: 20px; font-size: 18px; color: #555">There is no account associated with the email user_email, it may have been deleted</p>
            </div>
        </div>
    </body>
</html>"""
invalid_session = """<!DOCTYPE html>
<html>
    <head>
        <title>Custom Cloud Storage</title>
    </head>
    <body style="font-family: Arial; margin: 0; background-color: #f5f6fa">
        <header style="font-size: 24px; background-color: #1f2937; color: white; font-weight: bold; padding: 16px 32px">Custom Cloud Storage</header>
        <div style="height: calc(100vh - 60px); display: flex; justify-content: center; align-items: center">
            <div style="border-radius: 8px; background-color: white; padding: 30px; width: 400px; display: flex; align-items: center; justify-content: center; flex-direction: column; box-shadow: -4px 4px 10px rgba(0, 0, 0, 0.1)">
                <h2 style="margin-bottom: 20px">Invalid session</h2>
                <p style="text-align: center; margin-bottom: 20px; font-size: 18px; color: #555">Your session is no longer valid. It is possible that the account password has been changed. Redirecting to login page in 5 seconds</p>
            </div>
        </div>
    </body>
    <script>
        setTimeout(function() {window.location.href = "/login"}, 5000)
    </script>
</html>"""
awaiting_verification = """<!DOCTYPE html>
<html>
    <head>
        <title>Custom Cloud Storage</title>
    </head>
    <body style="font-family: Arial; margin: 0; background-color: #f5f6fa">
        <header style="font-size: 24px; background-color: #1f2937; color: white; font-weight: bold; padding: 16px 32px">Custom Cloud Storage</header>
        <div style="height: calc(100vh - 60px); display: flex; justify-content: center; align-items: center">
            <div style="border-radius: 8px; background-color: white; padding: 30px; width: 400px; display: flex; align-items: center; justify-content: center; flex-direction: column; box-shadow: -4px 4px 10px rgba(0, 0, 0, 0.1)">
                <h2 style="margin-bottom: 20px">Awaiting admin verification</h2>
                <p style="text-align: center; margin-bottom: 15px; font-size: 18px; color: #555">Please wait until an admin verifies your account in order to use Custom Cloud Storage</p>
                <p id="TryAgain" style="text-align: center; margin-bottom: 20px; font-size: 15px; color: #555">Trying again in 5 seconds</p>
            </div>
        </div>
    </body>
    <script>
        const TryAgain = document.getElementById("TryAgain")
        setTimeout(function() {TryAgain.textContent = "Trying again in 4 seconds"}, 1000)
        setTimeout(function() {TryAgain.textContent = "Trying again in 3 seconds"}, 2000)
        setTimeout(function() {TryAgain.textContent = "Trying again in 2 seconds"}, 3000)
        setTimeout(function() {TryAgain.textContent = "Trying again in 1 seconds"}, 4000)
        setTimeout(function() {window.location.href = "/home?path=/"}, 5000)
    </script>
</html>"""
app = Flask("Custom Cloud Storage")
data_folder_path = os.path.dirname(__file__) + "/Custom Cloud Storage Data"
email_ssl_context = ssl.create_default_context()
if not os.path.exists(data_folder_path):
    print("No data found in this folder")
    create_data_folder_path = input(f"Create data folder {data_folder_path}?: ")
    if create_data_folder_path == "Yes":
        os.mkdir(data_folder_path)
        os.mkdir(data_folder_path + "/Account Verification")
        os.mkdir(data_folder_path + "/Change Password Verification")
        os.mkdir(data_folder_path + "/Change Email 1")
        os.mkdir(data_folder_path + "/Change Email 2")
        secret_key = os.urandom(24)
        app.secret_key = secret_key
        sender_gmail = input("Enter your gmail (must be gmail not any other email serivce, required for verifying emails): ")
        sender_gmail_app_password = input("Enter your app password (visit https://support.google.com/mail/answer/185833?hl=en to find out how to get an app password for your gmail): ")
        json_file = open(data_folder_path + "/info.json", "w")
        json.dump({"secret_key": base64.b64encode(secret_key).decode(),"sender_gmail": sender_gmail, "sender_gmail_app_password": sender_gmail_app_password}, json_file, indent=4)
        json_file.close()
    else:
        if create_data_folder_path != "No":
            print("Invalid input")
        print("Closing program")
        time.sleep(3)
        exit()
else:
    json_file = open(data_folder_path + "/info.json", "r")
    json_data = json.load(json_file)
    json_file.close()
    app.secret_key = base64.b64decode(json_data["secret_key"].encode())
    sender_gmail = json_data["sender_gmail"]
    sender_gmail_app_password = json_data["sender_gmail_app_password"]
def ActualSendEmail(recipient_email, html_content):
    email = EmailMessage()
    email["Subject"] = "Custom Cloud Storage"
    email["From"] = sender_gmail
    email["To"] = recipient_email
    email.add_alternative(html_content, subtype="html")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=email_ssl_context) as smtp:
        smtp.login(sender_gmail, sender_gmail_app_password)
        smtp.send_message(email)
def SendEmail(recipient_email, html_content):
    Thread(target=ActualSendEmail, args=(recipient_email, html_content)).start()
@app.before_request
def before_request():
    if request.method == "GET":
        if request.path not in ["/signup", "/login", "/change_password", "/home", "/account_settings", "/change_email", "/delete_account"]:
            return redirect("/login")
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        if not "login_data" in session:
            signup_html = """<!DOCTYPE html>
<html>
    <head>
        <title>Custom Cloud Storage</title>
    </head>
    <body style="font-family: Arial; margin: 0; background-color: #f5f6fa">
        <header style="font-size: 24px; background-color: #1f2937; color: white; font-weight: bold; padding: 16px 32px">Custom Cloud Storage</header>
        <div id="SignupContainer" style="height: calc(100vh - 60px); display: flex; justify-content: center; align-items: center">
            <div style="border-radius: 8px; background-color: white; padding: 30px; width: 300px; display: flex; align-items: center; justify-content: center; flex-direction: column; box-shadow: -4px 4px 10px rgba(0, 0, 0, 0.1)">
                <h2 style="margin-bottom: 20px">Signup</h2>
                <form id="DataForm1" style="width: 100%">
                    <input id="email" type="email" name="email" placeholder="Enter your email" required style="width: 100%; padding: 10px; border-radius: 5px; border-width: 1px; border-color: #ccc; border-style: solid; margin-bottom: 20px; box-sizing: border-box">
                    <input id="password" type="password" name="password" placeholder="Enter your password" required style="width: 100%; padding: 10px; border-radius: 5px; border-width: 1px; border-color: #ccc; border-style: solid; margin-bottom: 20px; box-sizing: border-box">
                    <input id="ConfirmPassword" type="password" name="ConfirmPassword" placeholder="Enter your password again to confirm" required style="width: 100%; padding: 10px; border-radius: 5px; border-width: 1px; border-color: #ccc; border-style: solid; margin-bottom: 20px; box-sizing: border-box">
                    <button style="padding: 10px; background-color: #3b82f6; border-radius: 5px; border: none; font-size: 15px; color: white; cursor: pointer; width: 100%; margin-bottom: 15px" onmouseover="this.style.background='#2563eb'" onmouseout="this.style.background='#3b82f6'">Create new account</button>
                </form>
                <p style="margin: 0px">Already have an account? <a href="/login" style="all: unset; color: #3b82f6; font-weight: 600; cursor: pointer">Login now</a></p>
            </div>
        </div>
        <div id="VerificationContainer" style="height: calc(100vh - 60px); display: none; justify-content: center; align-items: center">
            <div style="border-radius: 8px; background-color: white; padding: 30px; width: 400px; display: flex; align-items: center; justify-content: center; flex-direction: column; box-shadow: -4px 4px 10px rgba(0, 0, 0, 0.1)">
                <h2 style="margin-bottom: 20px">Verification Required</h2>
                <p id="VerificationMessage" style="text-align: center; margin-bottom: 20px; font-size: 18px; color: #555"></p>
                <form id="DataForm2" style="width: 100%">
                    <input id="VerificationCode" placeholder="Enter the 6 digit verification code" required maxLength="6" style="width: 100%; padding: 10px; border-radius: 5px; border-width: 1px; border-color: #ccc; border-style: solid; margin-bottom: 20px; box-sizing: border-box; text-align: center">
                    <button id="VerifyButton" style="padding: 10px; background-color: #3b82f6; border-radius: 5px; border: none; font-size: 15px; color: white; cursor: pointer; width: 100%" onmouseover="this.style.background='#2563eb'" onmouseout="this.style.background='#3b82f6'">Verify</button>
                </form>
            </div>
        </div>
    </body>
    <script>
        const SignupContainer = document.getElementById("SignupContainer")
        const DataForm1 = document.getElementById("DataForm1")
        const email = document.getElementById("email")
        const password = document.getElementById("password")
        const ConfirmPassword = document.getElementById("ConfirmPassword")
        const VerificationContainer = document.getElementById("VerificationContainer")
        const VerificationMessage = document.getElementById("VerificationMessage")
        const VerificationCode = document.getElementById("VerificationCode")
        const VerifyButton = document.getElementById("VerifyButton")
        const DataForm2 = document.getElementById("DataForm2")
        function EnableForm(form) {
            for (let element of form.elements) {
                element.disabled = false
            }
        }
        function DisableForm(form) {
            for (let element of form.elements) {
                element.disabled = true
            }
        }
        DataForm1.addEventListener("submit", function(event) {
            event.preventDefault()
            DisableForm(DataForm1)
            if (password.value != ConfirmPassword.value) {
                alert("Passwords do not match")
                EnableForm(DataForm1)
            }
            else if (password.value.length < 5) {
                alert("Password must be atleast 5 characters long")
                EnableForm(DataForm1)
            }
            else {
                const package = new FormData()
                package.append("stage", "1")
                package.append("email", email.value)
                package.append("password", password.value)
                fetch("/signup", {method: "POST", body: package}).then(function(response) {
                    if (response.status == 200) {
                        SignupContainer.style.display = "none"
                        VerificationContainer.style.display = "flex"
                        VerificationMessage.textContent = "A verification code has been sent to " + email.value + ", please enter the code below to complete the signup process also make sure to check your spam folder"
                    }
                    else if (response.status == 301) {
                        alert("This email is already under use")
                        EnableForm(DataForm1)
                    }
                    else if (response.status == 302) {
                        alert("Password must be atleast 5 characters long")
                        EnableForm(DataForm1)
                    }
                    else {
                        alert("An unknown error occured")
                        EnableForm(DataForm1)
                    }
                })
            }
        })
        DataForm2.addEventListener("submit", function(event) {
            event.preventDefault()
            DisableForm(DataForm2)
            let isDigit = true
            for (let i=0; i<VerificationCode.value.length; i++) {
                if (VerificationCode.value[i] < "0" || VerificationCode.value[i] > "9") {
                    isDigit = false
                    break
                }
            }
            if (!isDigit) {
                alert("Please enter only numbers")
                EnableForm(DataForm2)
            }
            else if (VerificationCode.value.length != 6) {
                alert("Please enter a 6 digit verification code")
                EnableForm(DataForm2)
            }
            else {
                const package = new FormData()
                package.append("stage", "2")
                package.append("email", email.value)
                package.append("verification_code", VerificationCode.value)
                fetch("/signup", {method: "POST", body: package}).then(function(response) {
                    if (response.status == 200) {
                        window.location.href = "/home?path=/"
                    }
                    else if (response.status == 301) {
                        alert("Incorrect verification code")
                        EnableForm(DataForm2)
                    }
                    else {
                        alert("An unknown error occured")
                        EnableForm(DataForm2)
                    }
                })
            }
        })
    </script>
</html>"""
            return signup_html
        else:
            return redirect("/home?path=/")
    else:
        try:
            stage = request.form.get("stage")
            if stage == "1":
                user_email = request.form.get("email")
                if os.path.exists(data_folder_path + "/" + user_email):
                    return "", 301
                else:
                    user_password = request.form.get("password")
                    if len(user_password) < 5:
                        return "", 302
                    else:
                        verification_code = str(random.randint(100000, 999999))
                        if not os.path.exists(data_folder_path + "/Account Verification/" + user_email):
                            os.mkdir(data_folder_path + "/Account Verification/" + user_email)
                        json_file = open(data_folder_path + "/Account Verification/" + user_email + "/info.json", "w")
                        json.dump({"hashed_password": sha256(user_password.encode()).hexdigest(), "verification_code": verification_code}, json_file, indent=4)
                        json_file.close()
                        html_content = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background-color: #f5f6fa; margin: 0px; display: flex; justify-content: center">
    <div style="width: 100%; background-color: #fff; padding: 30px; border-radius: 12px; box-shadow: -4px 4px 10px rgba(0, 0, 0, 0.1); text-align: center">
        <h2 style="color: #1f2937">Verify Your Email</h2>
        <p style="font-size: 16px; color: #555">Hello! To complete your signup procedure, please use the verification code below</span></p>
        <p style="font-size: 22px; font-weight: bold; margin: 20px; letter-spacing: 4px; color: #3b82f6">{verification_code}</p>
    </div>
</body>
</html>"""
                        SendEmail(user_email, html_content)
                        return ""
            elif stage == "2":
                user_email = request.form.get("email")
                json_file = open(data_folder_path + "/Account Verification/" + user_email + "/info.json", "r")
                json_data = json.load(json_file)
                json_file.close()
                if request.form.get("verification_code") == json_data["verification_code"]:
                    os.mkdir(data_folder_path + "/" + user_email)
                    os.mkdir(data_folder_path + "/" + user_email + "/Data")
                    json_file = open(data_folder_path + "/" + user_email + "/info.json", "w")
                    session_id = sha256((user_email+json_data["hashed_password"]).encode()).hexdigest()
                    json.dump({"hashed_password": json_data["hashed_password"], "session_id": session_id, "admin_verified": False, "allocated_space_in_bytes": None, "used_space_in_bytes": 0, "created_at": datetime.fromtimestamp(time.time()).strftime("%d-%m-%Y %I:%M %p")}, json_file, indent=4)
                    json_file.close()
                    shutil.rmtree(data_folder_path + "/Account Verification/" + user_email)
                    session["login_data"] = [user_email, session_id]
                    return ""
                else:
                    return "", 301
            else:
                return "", 300
        except:
            return "", 300
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if "login_data" in session:
            return redirect("/home?path=/")
        else:
            login_html = """<!DOCTYPE html>
<html>
    <head>
        <title>Custom Cloud Storage</title>
    </head>
    <body style="font-family: Arial; margin: 0; background-color: #f5f6fa">
        <header style="font-size: 24px; background-color: #1f2937; color: white; font-weight: bold; padding: 16px 32px">Custom Cloud Storage</header>
        <div id="LoginContainer" style="height: calc(100vh - 60px); display: flex; justify-content: center; align-items: center">
            <div style="border-radius: 8px; background-color: white; padding: 30px; width: 300px; display: flex; align-items: center; justify-content: center; flex-direction: column; box-shadow: -4px 4px 10px rgba(0, 0, 0, 0.1)">
                <h2 style="margin-bottom: 20px">Login</h2>
                <form id="DataForm" style="width: 100%">
                    <input id="email" type="email" name="email" placeholder="Enter your email" required style="width: 100%; padding: 10px; border-radius: 5px; border-width: 1px; border-color: #ccc; border-style: solid; margin-bottom: 20px; box-sizing: border-box">
                    <input id="password" type="password" name="password" placeholder="Enter your password" required style="width: 100%; padding: 10px; border-radius: 5px; border-width: 1px; border-color: #ccc; border-style: solid; margin-bottom: 20px; box-sizing: border-box">
                    <button id="SubmitButton" style="padding: 10px; background-color: #3b82f6; border-radius: 5px; border: none; font-size: 15px; color: white; cursor: pointer; width: 100%; margin-bottom: 5px" onmouseover="this.style.background='#2563eb'" onmouseout="this.style.background='#3b82f6'">Login</button>
                </form>
                <p style="margin: 0px 0px 10px 0px; width: 100%; text-align: right; font-size: 14px"><a href="/change_password" style="all: unset; cursor: pointer">Forgot password?</a></p>
                <p style="margin: 0px">Don't have an account? <a href="/signup" style="all: unset; color: #3b82f6; font-weight: 600; cursor: pointer">Create now</a></p>
            </div>
        </div>
    </body>
    <script>
        const DataForm = document.getElementById("DataForm")
        const email = document.getElementById("email")
        const password = document.getElementById("password")
        function EnableForm(form) {
            for (let element of form.elements) {
                element.disabled = false
            }
        }
        function DisableForm(form) {
            for (let element of form.elements) {
                element.disabled = true
            }
        }
        DataForm.addEventListener("submit", function() {
            event.preventDefault()
            DisableForm(DataForm)
            const package = new FormData()
            package.append("email", email.value)
            package.append("password", password.value)
            fetch("/login", {method: "POST", body: package}).then(function(response) {
                if (response.status == 200) {
                    window.location.href = "/home?path=/"
                }
                else if (response.status == 301) {
                    alert("No account is associated with this email")
                    EnableForm(DataForm)
                }
                else if (response.status == 302) {
                    alert("Incorrect password")
                    EnableForm(DataForm)
                }
            })  
        })
    </script>
</html>"""
            return login_html
    else:
        try:
            user_email = request.form.get("email")
            password = request.form.get("password")
            if not os.path.exists(data_folder_path + "/" + user_email):
                return "", 301
            else:
                json_file = open(data_folder_path + "/" + user_email + "/info.json", "r")
                json_data = json.load(json_file)
                json_file.close()
                if json_data["hashed_password"] == sha256(password.encode()).hexdigest():
                    session["login_data"] = [user_email, json_data["session_id"]]
                    return ""
                else:
                    return "", 302
        except:
            return "", 300
@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if request.method == "GET":
        if "login_data" in session:
            return redirect("/home?path=/")
        else:
            change_password_html = """<!DOCTYPE html>
<html>
    <head>
        <title>Custom Cloud Storage</title>
    </head>
    <body style="font-family: Arial; margin: 0; background-color: #f5f6fa">
        <header style="font-size: 24px; background-color: #1f2937; color: white; font-weight: bold; padding: 16px 32px">Custom Cloud Storage</header>
        <div id="PasswordChangeContainer" style="height: calc(100vh - 60px); display: flex; justify-content: center; align-items: center">
            <div style="border-radius: 8px; background-color: white; padding: 30px; width: 300px; display: flex; align-items: center; justify-content: center; flex-direction: column; box-shadow: -4px 4px 10px rgba(0, 0, 0, 0.1)">
                <h2 style="margin-bottom: 20px">Change password</h2>
                <p style="text-align: center">Enter the email of the account whose password you forgot</p>
                <form id="DataForm1" style="width: 100%">
                    <input id="email" type="email" placeholder="Enter your email" required style="width: 100%; padding: 10px; border-radius: 5px; border-width: 1px; border-color: #ccc; border-style: solid; margin-bottom: 20px; box-sizing: border-box">
                    <button id="SubmitButton" style="padding: 10px; background-color: #3b82f6; border-radius: 5px; border: none; font-size: 15px; color: white; cursor: pointer; width: 100%" onmouseover="this.style.background='#2563eb'" onmouseout="this.style.background='#3b82f6'">Change Password</button>
                </form>
            </div>
        </div>
        <div id="VerificationContainer" style="height: calc(100vh - 60px); display: none; justify-content: center; align-items: center">
            <div style="border-radius: 8px; background-color: white; padding: 30px; width: 400px; display: flex; align-items: center; justify-content: center; flex-direction: column; box-shadow: -4px 4px 10px rgba(0, 0, 0, 0.1)">
                <h2 style="margin-bottom: 20px">Verification Required</h2>
                <p id="VerificationMessage" style="text-align: center; margin-bottom: 20px; font-size: 18px; color: #555">A verification code has been sent to example@gmail.com please enter the code below to change the password. Make sure to check your spam folder</p>
                <form id="DataForm2" style="width: 100%">
                    <input id="VerificationCode" placeholder="Enter the 6 digit verification code" required maxLength="6" style="width: 100%; padding: 10px; border-radius: 5px; border-width: 1px; border-color: #ccc; border-style: solid; margin-bottom: 20px; box-sizing: border-box">
                    <input id="password" type="password" placeholder="Enter your password" required style="width: 100%; padding: 10px; border-radius: 5px; border-width: 1px; border-color: #ccc; border-style: solid; margin-bottom: 20px; box-sizing: border-box">
                    <input id="ConfirmPassword" type="password" placeholder="Enter your password again to confirm" required style="width: 100%; padding: 10px; border-radius: 5px; border-width: 1px; border-color: #ccc; border-style: solid; margin-bottom: 20px; box-sizing: border-box">
                    <button id="VerifyButton" style="padding: 10px; background-color: #3b82f6; border-radius: 5px; border: none; font-size: 15px; color: white; cursor: pointer; width: 100%" onmouseover="this.style.background='#2563eb'" onmouseout="this.style.background='#3b82f6'">Verify</button>
                </form>
            </div>
        </div>
    </body>
    <script>
        const PasswordChangeContainer = document.getElementById("PasswordChangeContainer")
        const DataForm1 = document.getElementById("DataForm1")
        const email = document.getElementById("email")
        const VerificationContainer = document.getElementById("VerificationContainer")
        const VerificationMessage = document.getElementById("VerificationMessage")
        const DataForm2 = document.getElementById("DataForm2")
        const VerificationCode = document.getElementById("VerificationCode")
        const password = document.getElementById("password")
        const ConfirmPassword = document.getElementById("ConfirmPassword")
        function EnableForm(form) {
            for (let element of form.elements) {
                element.disabled = false
            }
        }
        function DisableForm(form) {
            for (let element of form.elements) {
                element.disabled = true
            }
        }
        DataForm1.addEventListener("submit", function(event) {
            event.preventDefault()
            DisableForm(DataForm1)
            const package = new FormData()
            package.append("stage", "1")
            package.append("email", email.value)
            fetch("/change_password", {method: "POST", body: package}).then(function(response) {
                if (response.status == 200) {
                    PasswordChangeContainer.style.display = "none"
                    VerificationContainer.style.display = "flex"
                    VerificationMessage.textContent = "A verification code has been sent to " + email.value + " please enter the code below to change the password. Make sure to check your spam folder"
                }
                else if (response.status == 301) {
                    alert("No account is associated with this email")
                    EnableForm(DataForm1)
                }
                else {
                    alert("An unknown error occured")
                    Enable(DataForm1)
                }
            })
        })
        DataForm2.addEventListener("submit", function(event) {
            event.preventDefault()
            DisableForm(DataForm2)
            let isDigit = true
            for (let i=0; i<VerificationCode.value.length; i++) {
                if (VerificationCode.value[i] < "0" || VerificationCode.value[i] > "9") {
                    isDigit = false
                    break
                }
            }
            if (!isDigit) {
                alert("Please enter only numbers as the verification code")
                EnableForm(DataForm2)
            }
            else if (VerificationCode.value.length != 6) {
                alert("Please enter a 6 digit verification code")
                EnableForm(DataForm2)
            }
            else if (password.value != ConfirmPassword.value) {
                alert("Passwords do not match")
                EnableForm(DataForm2)
            }
            else if (password.value.length < 5) {
                alert("Password must be atleast 5 characters long")
                EnableForm(DataForm2)
            }
            else {
                const package = new FormData()
                package.append("stage", "2")
                package.append("email", email.value)
                package.append("password", password.value)
                package.append("verification_code", VerificationCode.value)
                fetch("/change_password", {method: "POST", body: package}).then(function(response) {
                    if (response.status == 200) {
                        alert("Password changed successfully")
                        window.location.href = "/home?path=/"
                    }
                    else if (response.status == 301) {
                        alert("Incorrect verification code")
                        EnableForm(DataForm2)
                    }
                    else if (response.status == 302) {
                        alert("Password must be atleast 5 characters long")
                        EnableForm(DataForm2)
                    }
                    else {
                        alert("An unknown error occured")
                        EnableForm(DataForm2)
                    }
                })
            }
        })
    </script>
</html>"""
            return change_password_html
    else:
        try:
            stage = request.form.get("stage")
            if stage == "1":
                user_email = request.form.get("email")
                if not os.path.exists(data_folder_path + "/" + user_email):
                    return "", 301
                else:
                    verification_code = str(random.randint(100000, 999999))
                    if not os.path.exists(data_folder_path + "/Change Password Verification/" + user_email):
                        os.mkdir(data_folder_path + "/Change Password Verification/" + user_email)
                    json_file = open(data_folder_path + "/Change Password Verification/" + user_email + "/info.json", "w")
                    json.dump({"verification_code": verification_code}, json_file, indent=4)
                    json_file.close()
                    html_content = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background-color: #f5f6fa; margin: 0px; display: flex; justify-content: center">
    <div style="width: 100%; background-color: #fff; padding: 30px; border-radius: 12px; box-shadow: -4px 4px 10px rgba(0, 0, 0, 0.1); text-align: center">
        <h2 style="color: #1f2937">Password Change</h2>
        <p style="font-size: 16px; color: #555">Hello! To complete your password change procedure please use the verification code below</p>
        <p style="font-size: 22px; font-weight: bold; margin: 20px; letter-spacing: 4px; color: #3b82f6">{verification_code}</p>
    </div>
</body>
</html>"""
                    SendEmail(user_email, html_content)
                    return ""
            elif stage == "2":
                user_email = request.form.get("email")
                password = request.form.get("password")
                if len(password) < 5:
                    return "", 302
                else:
                    verification_code = request.form.get("verification_code")
                    json_file = open(data_folder_path + "/Change Password Verification/" + user_email + "/info.json", "r")
                    json_data = json.load(json_file)
                    json_file.close()
                    if json_data["verification_code"] == verification_code:
                        hashed_password = sha256(password.encode()).hexdigest()
                        session_id = sha256((user_email+hashed_password).encode()).hexdigest()
                        json_file = open(data_folder_path + "/" + user_email + "/info.json", "r")
                        json_data = json.load(json_file)
                        json_file.close()
                        json_data["hashed_password"] = hashed_password
                        json_data["session_id"] = session_id
                        json_file = open(data_folder_path + "/" + user_email + "/info.json", "w")
                        json.dump(json_data, json_file, indent=4)
                        json_file.close()
                        session["login_data"] = [user_email, session_id]
                        shutil.rmtree(data_folder_path + "/Change Password Verification/" + user_email)
                        html_content = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background-color: #f5f6fa; margin: 0px; display: flex; justify-content: center">
    <div style="width: 100%; background-color: #fff; padding: 30px; border-radius: 12px; box-shadow: -4px 4px 10px rgba(0, 0, 0, 0.1); text-align: center">
        <h2 style="color: #1f2937">Password Change</h2>
        <p style="font-size: 16px; color: #555">Your Custom Cloud Storage account's password has been successfully changed</p>
    </div>
</body>
</html>"""
                        SendEmail(user_email, html_content)
                        return ""
                    else:
                        return "", 301
            else:
                return "", 300
        except:
            return "", 300
@app.route("/get_dirname", methods=["POST"])
def get_dirname():
    try:
        user_email = session["login_data"][0]
        session_id = session["login_data"][1]
        json_file = open(data_folder_path + "/" + user_email + "/info.json", "r")
        json_data = json.load(json_file)
        json_file.close()
        if json_data["session_id"] == session_id:
            return os.path.dirname(request.form.get("path"))
        else:
            return "", 300
    except:
        return "", 300
@app.route("/verify_path", methods=["POST"])
def verify_path():
    try:
        user_email = session["login_data"][0]
        session_id = session["login_data"][1]
        json_file = open(data_folder_path + "/" + user_email + "/info.json", "r")
        json_data = json.load(json_file)
        json_file.close()
        if json_data["session_id"] == session_id:
            if os.path.isdir(data_folder_path + "/" + user_email + "/Data" + request.form.get("path")):
                return ""
            else:
                return "", 301
        else:
            return "", 300
    except:
        return "", 300
@app.route("/get_path", methods=["POST"])
def get_path():
    try:
        user_email = session["login_data"][0]
        session_id = session["login_data"][1]
        json_file = open(data_folder_path + "/" + user_email + "/info.json", "r")
        json_data = json.load(json_file)
        json_file.close()
        if json_data["session_id"] == session_id:
            return session["source_path"]
        else:
            return "", 300
    except:
        return "", 300
def get_folder_size(path):
    size = 0
    paths = [path]
    for path in paths:
        for item in os.scandir(path):
            if item.is_file():
                size += item.stat().st_size
            else:
                paths.append(item.path)
    return size
@app.route("/actions", methods = ["POST"])
def actions():
    try:
        user_email = session["login_data"][0]
        session_id = session["login_data"][1]
        json_file = open(data_folder_path + "/" + user_email + "/info.json", "r")
        json_data = json.load(json_file)
        json_file.close()
        if json_data["session_id"] == session_id:
            request_type = request.args.get("type")
            user_data_folder_path = data_folder_path + "/" + user_email + "/Data"
            if request_type == "download":
                return send_file(user_data_folder_path + request.form.get("path"), as_attachment=True)
            elif request_type == "rename":
                path = user_data_folder_path + request.form.get("path")
                new_path = os.path.join(os.path.dirname(path) + "/" + request.form.get("new_name"))
                os.rename(path, new_path)
                return ""
            elif request_type == "copy_set":
                session["source_path"] = "Copy:" + request.form.get("path")
                return ""
            elif request_type == "copy":
                currentfolderpath = user_data_folder_path + request.form.get("current_folder_path")
                source_path = user_data_folder_path + session["source_path"].removeprefix("Copy:")
                session.pop("source_path")
                if os.path.isdir(source_path):
                    destination_path = currentfolderpath + "/" + source_path.split("/")[-1] + " (Copy)"
                    if os.path.exists(destination_path):
                        return "", 301
                    else:
                        folder_size = get_folder_size(source_path)
                        if folder_size <= json_data["allocated_space_in_bytes"] - json_data["used_space_in_bytes"]:
                            shutil.copytree(source_path, destination_path)
                            total_copy_size = folder_size
                        else:
                            return "", 302
                else:
                    file_size = Path(source_path).stat().st_size
                    destination_path = currentfolderpath + "/" + source_path.split("/")[-1].split(".")[0] + " (Copy)" + "." + source_path.split("/")[-1].split(".")[1]
                    if os.path.exists(destination_path):
                        return "", 301
                    else:
                        if file_size <= json_data["allocated_space_in_bytes"] - json_data["used_space_in_bytes"]:
                            shutil.copy(source_path, destination_path)
                            total_copy_size = file_size
                        else:
                            return "", 302
                json_data["used_space_in_bytes"] += total_copy_size
                json_file = open(data_folder_path + "/" + user_email + "/info.json", "w")
                json.dump(json_data, json_file, indent=4)
                json_file.close()
                return ""
            elif request_type == "mass_copy_set":
                session["source_path"] = "MassCopy:" + str(request.form.get("paths"))
                return ""
            elif request_type == "mass_copy":
                currentfolderpath = user_data_folder_path + request.form.get("current_folder_path")
                source_paths = session["source_path"].removeprefix("MassCopy:").split(",")
                total_copy_size = 0
                duplicates = []
                for i in range(len(source_paths)):
                    source_path = user_data_folder_path + source_paths[i]
                    source_paths[i] = source_path
                    if os.path.isdir(source_path):
                        new_folder_name = source_path.split("/")[-1] + " (Copy)"
                        if os.path.exists(currentfolderpath + "/" + new_folder_name):
                            duplicates.append(new_folder_name)
                        else:
                            total_copy_size += get_folder_size(source_path)
                    else:
                        new_file_name = source_path.split("/")[-1].split(".")[0] + " (Copy)" + "." + source_path.split("/")[-1].split(".")[1]
                        if os.path.exists(currentfolderpath + "/" + new_file_name):
                            duplicates.append(new_file_name)
                        else:
                            total_copy_size += Path(source_path).stat().st_size
                session.pop("source_path")
                if len(duplicates) == 0:
                    if total_copy_size <= json_data["allocated_space_in_bytes"] - json_data["used_space_in_bytes"]:
                        for source_path in source_paths:
                            if os.path.isdir(source_path):
                                shutil.copytree(source_path, currentfolderpath + "/" + source_path.split("/")[-1] + " (Copy)")
                            else:
                                shutil.copy(source_path, currentfolderpath + "/" + source_path.split("/")[-1].split(".")[0] + " (Copy)" + "." + source_path.split("/")[-1].split(".")[1])
                        json_data["used_space_in_bytes"] += total_copy_size
                        json_file = open(data_folder_path + "/" + user_email + "/info.json", "w")
                        json.dump(json_data, json_file, indent=4)
                        json_file.close()
                        return ""
                    else:
                        return "", 302
                else:
                    return jsonify(duplicates), 301
            elif request_type == "move_set":
                session["source_path"] = "Move:" + request.form.get("path")
                return ""
            elif request_type == "move":
                source_path = user_data_folder_path + session["source_path"].removeprefix("Move:")
                currentfolderpath = user_data_folder_path + request.form.get("current_folder_path")
                session.pop("source_path")
                if os.path.exists(currentfolderpath + "/" + source_path.split("/")[-1]):
                    return "", 301
                else:
                    shutil.move(source_path, currentfolderpath)
                    return ""
            elif request_type == "mass_move_set":
                session["source_path"] = "MassMove:" + str(request.form.get("paths"))
                return ""
            elif request_type == "mass_move":
                currentfolderpath = user_data_folder_path + request.form.get("current_folder_path")
                source_paths = session["source_path"].removeprefix("MassMove:").split(",")
                session.pop("source_path")
                duplicates = []
                for i in range(len(source_paths)):
                    source_path = user_data_folder_path + source_paths[i]
                    source_paths[i] = source_path
                    new_path = source_path.split("/")[-1]
                    if os.path.exists(currentfolderpath + "/" + new_path):
                        duplicates.append(new_path)
                if len(duplicates) == 0:
                    for source_path in source_paths:
                        if os.path.dirname(source_path) == currentfolderpath:
                            return ""
                        else:
                            shutil.move(source_path, currentfolderpath)
                            return ""
                else:
                    return jsonify(duplicates), 301
            elif request_type == "delete":
                path = user_data_folder_path + request.form.get("path")
                if os.path.isdir(path):
                    folder_size = get_folder_size(path)
                    shutil.rmtree(path)
                    total_delete_size = folder_size
                else:
                    file_size = Path(path).stat().st_size
                    os.remove(path)
                    total_delete_size = file_size
                json_data["used_space_in_bytes"] -= total_delete_size
                json_file = open(data_folder_path + "/" + user_email + "/info.json", "w")
                json.dump(json_data, json_file, indent=4)
                json_file.close()
                return ""
            elif request_type == "mass_delete":
                total_delete_size = 0
                for path in request.form.get("paths").split(","):
                    path = user_data_folder_path + path
                    if os.path.isdir(path):
                        folder_size = get_folder_size(path)
                        shutil.rmtree(path)
                        total_delete_size += folder_size
                    else:
                        file_size = Path(path).stat().st_size
                        os.remove(path)
                        total_delete_size += file_size
                json_data["used_space_in_bytes"] -= total_delete_size
                json_file = open(data_folder_path + "/" + user_email + "/info.json", "w")
                json.dump(json_data, json_file, indent=4)
                json_file.close()
                return ""
        else:
            return "", 300
    except:
        return "", 300
def FormatedSize(bytes):
    if bytes < 1000:
        return f"{bytes} B"
    elif bytes < 1000**2:
        return f"{bytes / 1000:.2f} KB"
    elif bytes < 1000**3:
        return f"{bytes / 1000**2:.2f} MB"
    else:
        return f"{bytes / 1000**3:.2f} GB"
@app.route("/home", methods=["GET", "POST"])
def home():
    if request.method == "GET":
        if not "login_data" in session:
            return redirect("/login")
        else:
            user_email = session["login_data"][0]
            if not os.path.exists(data_folder_path + "/" + user_email):
                session.clear()
                return account_not_found.replace("user_email", user_email)
            else:
                json_file = open(data_folder_path + "/" + user_email + "/info.json")
                json_data = json.load(json_file)
                json_file.close()
                if json_data["session_id"] != session["login_data"][1]:
                    session.clear()
                    return invalid_session
                else:
                    if not (json_data["admin_verified"] and json_data["allocated_space_in_bytes"] is not None):
                        return awaiting_verification
                    else:
                        path = request.args.get("path")
                        if not path:
                            return redirect("/home?path=/")
                        else:
                            home_html = """<!DOCTYPE html>
<html>
    <head>
        <title>Custom Cloud Storage</title>
    </head>
    <body style="font-family: Arial; margin: 0; background-color: #f5f6fa">
        <header style="font-size: 24px; background-color: #1f2937; color: white; font-weight: bold; padding: 16px 32px">Custom Cloud Storage</header>
        <div id = "SelectionBox" style="position: absolute; border: 1px solid #3399ff; background-color: rgba(51, 153, 255, 0.35); display: none; top: 0px; left: 0px"></div>
        <div style="margin: 24px 32px 15px 32px; display: flex; align-items: center">
            <p style="margin: 0px; font-size: 18px; color: #374151; font-weight: bold; letter-spacing: 0.5px">Text2FromPython</p>
            <div style="flex: 1"></div>
            <button id="AccountSettings" style="cursor: pointer; padding: 10px; background-color: #3b82f6; color: white; border: none; border-radius: 15px; width: 170px; font-size: 15px" onmouseover="this.style.background='#2563eb'" onmouseout="this.style.background='#3b82f6'">Account Settings</button>
        </div>
        <div style="margin: 0px 32px 15px 32px; display: flex; justify-content: center; align-items: center; gap: 8px">
            <button id="UpButton" style="padding: 8px; border-radius: 5px; border: none; background-color: #3b82f6; color: white; cursor: pointer; width: 50px" onmouseover="this.style.background='#2563eb'" onmouseout="this.style.background='#3b82f6'">⬆</button>
            <input id="CurrentFolderPath" type="text" value="CurrentFolderPathFromPython" style="flex: 1; padding: 8px; border-radius: 5px; border-width: 1px; border-style: solid; border-color: #ccc; height: 18px; font-size: 16px">
            <div style="position: relative">
                <button id="UploadButton" style="padding: 8px; border-radius: 5px; border: none; background-color: #f97316; color: white; cursor: pointer; width: 100px" onmouseover="this.style.background='#ea580c'" onmouseout="this.style.background='#f97316'">Upload</button>
                <div id="UploadMenu" style="display: none; position: absolute; top: 32px; width: 100%; background-color: white; box-shadow: -4px 4px 10px rgba(0, 0, 0, 0.1); border-radius: 5px; z-index: 1">
                    <div style="padding: 8px; cursor: pointer" onclick="FilesInputSection.click()" onmouseover="this.style.background='#f4f4f4'" onmouseout="this.style.background='white'">Upload File</div>
                    <div style="padding: 8px; cursor: pointer" onclick="FolderInputSection.click()" onmouseover="this.style.background='#f4f4f4'" onmouseout="this.style.background='white'">Upload Folder</div>
                </div>
            </div>
        </div>
        <input id="SearchBar" type="text" placeholder="Search" style="margin: 0px 32px 15px 32px; width: calc(100% - 82px); padding: 8px; border-radius: 5px; border-width: 1px; border-style: solid; border-color: #ccc; height: 18px; font-size: 16px">
        <div id="ProgressBarContainer" style="position: relative; background-color: #e5e7eb; display: none; margin: 0px 32px 15px 32px; border-radius: 5px; height: 20px; z-index: 0">
            <div id="ProgressBar" style="background-color: #83e559; width: 0%; height: 100%; border-radius: 5px"></div>
            <div id="ProgressPercentage" style="position: absolute; top: 0; height: 100%; width: 100%; display: flex; align-items: center; justify-content: center">0%</div>
        </div>
        <button id="CopyMoveButton" style="display: DisplayFromPython; margin: 0px 0px 15px 32px; padding: 10px 12px; background-color: #4caf50; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer" onmouseover="this.style.background='#45a049'" onmouseout="this.style.background='#4CAF50'">Text1FromPython</button>
        <div id="MassActionButtons" style="margin: 0px 0px 15px 32px; visibility: hidden">
            <button id="MassActionDownloadButton" style="padding: 6px 12px; font-size: 15px; border-radius: 6px; border: none; background-color: #10b981; color: white; cursor: pointer; margin-right: 4px" onmouseover="this.style.background='#059669'" onmouseout="this.style.background='#10b981'">Download</button>
            <button id="MassActionRenameButton" style="padding: 6px 12px; font-size: 15px; border-radius: 6px; border: none; background-color: #ffce50; color: white; cursor: pointer; margin-right: 4px" onmouseover="this.style.background='#f59e0b'" onmouseout="this.style.background='#fbbf24'">Rename</button>
            <button id="MassActionCopyButton" style="padding: 6px 12px; font-size: 15px; border-radius: 6px; border: none; background-color: #3b82f6; color: white; cursor: pointer; margin-right: 4px" onmouseover="this.style.background='#2563eb'" onmouseout="this.style.background='#3b82f6'">Copy</button>
            <button id="MassActionMoveButton" style="padding: 6px 12px; font-size: 15px; border-radius: 6px; border: none; background-color: #6366f1; color: white; cursor: pointer; margin-right: 4px" onmouseover="this.style.background='#4f46e5'" onmouseout="this.style.background='#6366f1'">Move</button>
            <button id="MassActionDeleteButton" style="padding: 6px 12px; font-size: 15px; border-radius: 6px; border: none; background-color: #ef4444; color: white; cursor: pointer; margin-right: 15px" onmouseover="this.style.background='#b91c1c'" onmouseout="this.style.background='#ef4444'">Delete</button>
            <span id="SelectedItemsCounter" style="font-weight: bold">Selected items:</span>
        </div>
        <input type="file" id="FilesInputSection" style="display: none" multiple name="FilesInputSection">
        <input type="file" id="FolderInputSection" style="display: none" webkitdirectory name="FolderInputSection">
        <div style="margin: 0px 32px 0px 32px; border-top-left-radius: 5px; border-top-right-radius: 5px">
            <div style="display: flex; flex-direction: row; background-color: #e5e7eb; padding: 12px">
                <span style="width: 400px; font-weight: bold">Name</span>
                <span style="width: 250px; font-weight: bold">Last modified</span>
                <span style="width: 140px; font-weight: bold">Size</span>
                <span style="font-weight: bold">Actions</span>
            </div>
            <div id="FilesList"></div>
        </div>
FilesFromFolderFromPython
        <div id="NoResults" style="display: none; justify-content: center; align-items: center; height: 485px">
            <div style="background-color: #f9fafb; color: #374151; padding: 20px 30px; border-radius: 8px; font-size: 18px; font-weight: bold; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1)">No results</div>
        </div>
    </body>
    <script>
        let x = 0
        let y = 0
        const SelectionBox = document.getElementById("SelectionBox")
        document.addEventListener("mousedown", function (event) {
            if (event.button == 0 && event.target.tagName == "BODY") {
                if (SelectionBox.style.display == "none") {
                    SelectionBox.style.top = event.pageY + "px"
                    SelectionBox.style.left = event.pageX + "px"
                    SelectionBox.style.width = "0px"
                    SelectionBox.style.height = "0px"
                    SelectionBox.style.display = "block"
                    x = event.pageX
                    y = event.pageY
                    document.body.style.userSelect = "none"
                }
            }
        })
        document.addEventListener("mouseup", function(event) {
            if (event.button === 0) {
                SelectionBox.style.display = "none"
                document.body.style.userSelect = "auto"
            }
        })
        function overlapping(selection_box, div_rect) {
            return !(selection_box.right < div_rect.left || selection_box.left > div_rect.right || selection_box.bottom < div_rect.top || selection_box.top > div_rect.bottom)
        }
        const FilesList = document.getElementById("FilesList")
        document.addEventListener("mousemove", function (event) {
            if (SelectionBox.style.display == "block") {
                const left = Math.min(x, event.pageX)
                const top = Math.min(y, event.pageY)
                let width = Math.abs(event.pageX - x)
                let height = Math.abs(event.pageY - y)
                const PageWidth = document.body.offsetWidth - 2
                const PageHeight = document.body.offsetHeight - 2
                if (left + width > PageWidth) {
                    width = PageWidth - left
                }
                if (top + height > PageHeight) {
                    height = PageHeight - top
                }
                SelectionBox.style.top = top + "px"
                SelectionBox.style.left = left + "px"
                SelectionBox.style.width = width + "px"
                SelectionBox.style.height = height + "px"
                if (event.clientY < 20) {
                    window.scrollBy(0, -20)
                } else if (event.clientY > window.innerHeight - 20) {
                    window.scrollBy(0, 20)
                }
                const file_elements = FilesList.children
                for (let i = 0; i < file_elements.length; i++) {
                    if (overlapping(SelectionBox.getBoundingClientRect(), file_elements[i].getBoundingClientRect())) {
                        const checkbox = file_elements[i].children[0].children[0]
                        if (!checkbox.checked) {
                            checkbox.checked = true
                            checkbox.style.opacity = 1
                            checkbox.dispatchEvent(new Event("change", {bubbles: true}))
                        }
                    }
                }
            }
        })
        let SelectionMode = "Select All"
        document.addEventListener("keydown", function (event) {
            if (document.activeElement.id != "SearchBar" && document.activeElement.id != "CurrentFolderPath") {
                event.preventDefault()
                let temp_file_elements = FilesList.children
                let file_elements = []
                for (let i = 0; i < temp_file_elements.length; i++) {
                    if (temp_file_elements[i].style.display != "none") {
                        file_elements.push(temp_file_elements[i])
                    }
                }
                temp_file_elements = []
                if (event.ctrlKey && event.key == "a") {
                    if (SelectionMode == "Select All") {
                        for (let i = 0; i < file_elements.length; i++) {
                            const checkbox = file_elements[i].children[0].children[0]
                            if (!checkbox.checked) {
                                checkbox.checked = true
                                checkbox.style.opacity = 1
                                checkbox.dispatchEvent(new Event("change", {bubbles: true}))
                            }
                        }
                        SelectionMode = "Deselect All"
                    }
                    else {
                        for (let i = 0; i < file_elements.length; i++) {
                            const checkbox = file_elements[i].children[0].children[0]
                            if (checkbox.checked) {
                                checkbox.checked = false
                                checkbox.style.opacity = 0
                                checkbox.dispatchEvent(new Event("change", {bubbles: true}))
                            }
                        }
                        SelectionMode = "Select All"
                    }
                }
                else if (event.ctrlKey && event.key == "A") {
                    for (let i = 0; i < file_elements.length; i++) {
                        const checkbox = file_elements[i].children[0].children[0]
                        if (checkbox.checked) {
                            checkbox.checked = false
                            checkbox.style.opacity = 0
                        }
                        else {
                            checkbox.checked = true
                            checkbox.style.opacity = 1
                        }
                        checkbox.dispatchEvent(new Event("change", {bubbles: true}))
                    }
                }
            }
        })
        const AccountSettings = document.getElementById("AccountSettings")
        AccountSettings.onclick = function() {
            window.location.href = "/account_settings"
        }
        const CurrentFolderPath = document.getElementById("CurrentFolderPath")
        const UpButton = document.getElementById("UpButton")
        UpButton.onclick = function() {
            while (CurrentFolderPath.value.includes("//")) {
                CurrentFolderPath.value = CurrentFolderPath.value.replace("//", "/")
            }
            if (CurrentFolderPath.value.endsWith("/")) {
                CurrentFolderPath.value = CurrentFolderPath.value.substring(0, CurrentFolderPath.value.length - 1)
            }
            if (CurrentFolderPath.value == "") {
                CurrentFolderPath.value = "/"
            }
            const package = new FormData()
            package.append("path", CurrentFolderPath.value)
            fetch("/get_dirname", {method: "POST", body: package}).then(async function(response) {
                if (response.status == 200) {
                    window.location.href = "/home?path=" + encodeURIComponent(await response.text())
                }
                else {
                    alert("An unknown error occured")
                }
            })
        }
        CurrentFolderPath.addEventListener("keydown", function(event) {
            if (event.key == "Enter") {
                while (CurrentFolderPath.value.includes("//")) {
                    CurrentFolderPath.value = CurrentFolderPath.value.replace("//", "/")
                }
                if (CurrentFolderPath.value.endsWith("/")) {
                    CurrentFolderPath.value = CurrentFolderPath.value.substring(0, CurrentFolderPath.value.length - 1)
                }
                if (CurrentFolderPath.value == "") {
                    CurrentFolderPath.value = "/"
                }
                const package = new FormData()
                package.append("path", CurrentFolderPath.value)
                fetch("/verify_path", {method: "POST", body: package}).then(function(response) {
                    if (response.status == 200) {
                        window.location.href = "/home?path=" + encodeURIComponent(CurrentFolderPath.value)
                    } 
                    else if (response.status == 301) {
                        alert("Invalid Path")
                    }
                    else {
                        alert("An unknown error occured")
                    }
                })
            }
        })
        const UploadMenu = document.getElementById("UploadMenu")
        document.getElementById("UploadButton").onclick = function() {
            if (UploadMenu.style.display == "none") {
                UploadMenu.style.display = "block"
            } else {
                UploadMenu.style.display = "none"
            }
        }
        document.addEventListener("click", function(event) {
            if (!UploadButton.contains(event.target) && !UploadMenu.contains(event.target)) {
                UploadMenu.style.display = "none"
            }
        })
        const SearchBar = document.getElementById("SearchBar")
        const NoResults = document.getElementById("NoResults")
        SearchBar.addEventListener("input", function() {
            file_elements = FilesList.children
            hidden_files = 0
            query = SearchBar.value.trim().toLowerCase()
            if (query == "") {
                for (let i = 0; i < file_elements.length; i++) {
                    file_elements[i].style.display = "flex"
                }
                NoResults.style.display = "none"
            }
            else {
                for (let i = 0; i < file_elements.length; i++) {
                    if (file_elements[i].children[0].textContent.replace(file_elements[i].children[0].children[1].textContent, "").trim().toLowerCase().includes(query)) {
                        file_elements[i].style.display = "flex"
                    }
                    else {
                        file_elements[i].style.display = "none"
                        hidden_files += 1
                    }
                }
                if (hidden_files == file_elements.length) {
                    NoResults.style.display = "flex"
                }
                else {
                    NoResults.style.display = "none"
                }
            }
        })
        const ProgressBarContainer = document.getElementById("ProgressBarContainer")
        const ProgressBar = document.getElementById("ProgressBar")
        const ProgressPercentage = document.getElementById("ProgressPercentage")
        function UpdateProgressBar(percentage) {
            ProgressBar.style.width = percentage + "%"
            ProgressPercentage.textContent = percentage + "%"
        }
        const CopyMoveButton = document.getElementById("CopyMoveButton")
        CopyMoveButton.onclick = function() {
            fetch("/get_path", {method: "POST"}).then(async function(response) {
                if (response.status == 200) {
                    let action = ""
                    let action_string = ""
                    const ResponseText = await response.text()
                    if (ResponseText.startsWith("Copy")) {
                        action = "copy"
                        action_string = "copying"
                        CopyMoveButton.textContent = "Copying..."
                    }
                    else if (ResponseText.startsWith("MassCopy")) {
                        action = "mass_copy"
                        action_string = "copying"
                        CopyMoveButton.textContent = "Copying..."
                    }
                    else if (ResponseText.startsWith("MassMove")) {
                        action = "mass_move"
                        action_string = "copying"
                        CopyMoveButton.textContent = "Moving"
                    }
                    else {
                        action = "move"
                        action_string = "moving"
                        CopyMoveButton.textContent = "Moving..."
                    }
                    const package = new FormData()
                    package.append("current_folder_path", CurrentFolderPath.value)
                    fetch("/actions?type=" + action, {method: "POST", body: package}).then(async function(response) {
                        if (response.status == 200) {
                            alert("Completed " + action_string + " all files / folders")
                        } 
                        else if (response.status == 301) {
                            if (action.startsWith("mass")) {
                                const failed_files = await response.json()
                                alert("The following files / folders already exist in this folder:\\n" + failed_files.join("\\n"))
                            }
                            else {
                                alert("This file / folder already exists in this folder")
                            }
                        }
                        else if (response.status == 302) {
                            alert("Not enough space")
                        }
                        else {
                            alert("An unknown error occured")
                        }
                        window.location.href = "/home?path=" + encodeURIComponent(CurrentFolderPath.value)
                    })
                }
                else {
                    alert("An unknown error occured")
                }
            })
        }
        const RemainingSpaceInBytes = RemainingSpaceInBytesFromPython
        let uploading = false
        function UploadFiles(files) {
            if (uploading) {
                alert("An upload is already under progress, please wait until it is over")
            }
            else {
                if (files.length != 0) {
                    let TotalUploadSizeInBytes = 0
                    for (let i=0; i<files.length; i++) {
                        TotalUploadSizeInBytes += files[i].size
                    }
                    if (TotalUploadSizeInBytes > RemainingSpaceInBytes) {
                        alert("Not enough space")
                    }
                    else {
                        uploading = true
                        ProgressBarContainer.style.display = "block"
                        const package = new FormData()
                        for (let file of files) {
                            package.append("Files", file)
                        }
                        const xhr = new XMLHttpRequest()
                        while (CurrentFolderPath.value.includes("//")) {
                            CurrentFolderPath.value = CurrentFolderPath.value.replace("//", "/")
                        }
                        if (CurrentFolderPath.value.endsWith("/")) {
                            CurrentFolderPath.value = CurrentFolderPath.value.substring(0, CurrentFolderPath.value.length - 1)
                        }
                        if (CurrentFolderPath.value == "") {
                            CurrentFolderPath.value = "/"
                        }
                        xhr.open("POST", "/home?path=" + CurrentFolderPath.value, true)
                        xhr.upload.onprogress = function(event) {
                            if (event.lengthComputable) {
                                UpdateProgressBar(Math.round((event.loaded / event.total) * 100))
                            }
                        }
                        xhr.onload = function() {
                            UpdateProgressBar(100)
                            if (xhr.status == 200) {
                                alert("Upload completed")
                                window.location.href = "/home?path=" + encodeURIComponent(CurrentFolderPath.value)
                            }
                            else if (xhr.status == 301) {
                                alert("Not enough storage")
                                uploading = false
                            }
                            else {
                                alert("An unknown error occured")
                                uploading = false
                            }
                            UpdateProgressBar(0)
                            ProgressBarContainer.style.display = "none"
                        }
                        xhr.send(package)
                    }
                }
            }
        }
        const FilesInputSection = document.getElementById("FilesInputSection")
        const FolderInputSection = document.getElementById("FolderInputSection")
        FilesInputSection.addEventListener("change", function() {
            UploadFiles(FilesInputSection.files)
        })
        FolderInputSection.addEventListener("change", function() {
            UploadFiles(FolderInputSection.files)
        })
        document.querySelectorAll("file").forEach(function(file) {
            const file_element_icon = file.getAttribute("icon")
            const file_element_name = file.getAttribute("name")
            const file_element_last_modified = file.getAttribute("last_modified")
            const file_element_size = file.getAttribute("size")
            const file_element = document.createElement("div")
            file_element.style.cssText = "background-color: white; display: flex; align-items: center; flex-direction: row; padding: 12px; border-bottom: 1px solid #ddd"
            let inner_html = `<div style="display: flex; align-items: center; width: 400px">
    <input type="checkbox" style="display: block; opacity: 0; transition: opacity 0.2s; margin-right: 8px">
    <span style="font-size: 24px; margin-right: 8px">${file_element_icon}</span>
    ${file_element_name}
</div>
<span style="width: 250px">${file_element_last_modified}</span>
<span style="width: 140px">${file_element_size}</span>
<button style="padding: 6px 12px; font-size: 15px; border-radius: 6px; border: none; background-color: #10b981; color: white; cursor: pointer; margin-right: 4px" onmouseover="this.style.background='#059669'" onmouseout="this.style.background='#10b981'">Download</button>
<button style="padding: 6px 12px; font-size: 15px; border-radius: 6px; border: none; background-color: #ffce50; color: white; cursor: pointer; margin-right: 4px" onmouseover="this.style.background='#f59e0b'" onmouseout="this.style.background='#fbbf24'">Rename</button>
<button style="padding: 6px 12px; font-size: 15px; border-radius: 6px; border: none; background-color: #3b82f6; color: white; cursor: pointer; margin-right: 4px" onmouseover="this.style.background='#2563eb'" onmouseout="this.style.background='#3b82f6'">Copy</button>
<button style="padding: 6px 12px; font-size: 15px; border-radius: 6px; border: none; background-color: #6366f1; color: white; cursor: pointer; margin-right: 4px" onmouseover="this.style.background='#4f46e5'" onmouseout="this.style.background='#6366f1'">Move</button>
<button style="padding: 6px 12px; font-size: 15px; border-radius: 6px; border: none; background-color: #ef4444; color: white; cursor: pointer" onmouseover="this.style.background='#b91c1c'" onmouseout="this.style.background='#ef4444'">Delete</button>`
            if (file_element_icon == "📁") {
                inner_html = inner_html.replace(`<button style="padding: 6px 12px; font-size: 15px; border-radius: 6px; border: none; background-color: #10b981; color: white; cursor: pointer; margin-right: 4px" onmouseover="this.style.background='#059669'" onmouseout="this.style.background='#10b981'">Download</button>`, "")
            }
            file_element.innerHTML = inner_html
            const checkbox = file_element.children[0].children[0]
            file_element.onmouseover = function() {
                file_element.style.background = "#f9fafb"
                if (!checkbox.checked) {
                    checkbox.style.opacity = 1
                }
            }
            file_element.onmouseout = function() {
                file_element.style.background = "white"
                if (!checkbox.checked) {
                    checkbox.style.opacity = 0
                }
            }
            FilesList.appendChild(file_element)
        })
        const MassActionButtons = document.getElementById("MassActionButtons")
        const MassActionDownloadButton = document.getElementById("MassActionDownloadButton")
        const MassActionRenameButton = document.getElementById("MassActionRenameButton")
        const MassActionCopyButton = document.getElementById("MassActionCopyButton")
        const MassActionMoveButton = document.getElementById("MassActionMoveButton")
        const MassActionDeleteButton = document.getElementById("MassActionDeleteButton")
        let checked_files = []
        const SelectedItemsCounter = document.getElementById("SelectedItemsCounter")
        FilesList.addEventListener("change", function(event) {
            if (event.target.type == "checkbox") {
                const checkbox = event.target
                const inner_div = checkbox.parentElement
                const file_icon = inner_div.children[1].textContent
                const file_name = inner_div.textContent.replace(file_icon, "").trim()
                const file_key = file_icon + " " + file_name
                if (checkbox.checked) {
                    checked_files.push(file_icon + " " + file_name)
                } 
                else {
                    checked_files.splice(checked_files.indexOf(file_icon + " " + file_name), 1)
                }
                if (checked_files.length == 0) {
                    MassActionButtons.style.visibility = "hidden"
                    SelectedItemsCounter.textContent = "Selected Items:"
                } else {
                    MassActionButtons.style.visibility = "visible"
                    SelectedItemsCounter.textContent = "Selected Items: " + checked_files.length
                }
                if (checked_files.length == 1) {
                    MassActionRenameButton.style.display = "inline-block"
                } else {
                    MassActionRenameButton.style.display = "none"
                }
                MassActionDownloadButton.style.display = "inline-block"
                for (let i = 0; i < checked_files.length; i++) {
                    if (checked_files[i].startsWith("📁")) {
                        MassActionDownloadButton.style.display = "none"
                        break
                    }
                }
            }
        })
        MassActionDownloadButton.onclick = function() {
            MassActionDownloadButton.disabled = true
            const file_elements = FilesList.children
            for (let i=0; i<checked_files.length; i++) {
                for (let j=0; j<file_elements.length; j++) {
                    const inner_div = file_elements[j].children[0]
                    const file_icon = inner_div.children[1].textContent
                    const file_name = inner_div.textContent.replace(file_icon, "").trim()
                    if (file_name == checked_files[i].split(" ").splice(1).join(" ")) {
                        setTimeout(function() {
                            file_elements[j].children[3].click()
                            if (i == checked_files.length - 1) {
                                MassActionDownloadButton.disabled = false
                            }
                        }, 200 * i)
                        break
                    }
                }
            }
        }
        MassActionRenameButton.onclick = function() {
            const file_name = checked_files[0].split(" ").splice(1).join(" ")
            const file_elements = FilesList.children
            for (let i=0; i<file_elements.length; i++) {
                const inner_div = file_elements[i].children[0]
                const file_element_icon = inner_div.children[1].textContent
                const file_element_name = inner_div.textContent.replace(file_element_icon, "").trim()
                if (file_element_name == file_name) {
                    file_elements[i].children[4].click()
                    break
                }
            }
        }
        MassActionCopyButton.onclick = function() {
            let paths = []
            for (let i=0; i<checked_files.length; i++) {
                paths.push(CurrentFolderPath.value + "/" + checked_files[i].split(" ").splice(1).join(" "))
            }
            const package = new FormData()
            package.append("paths", paths)
            fetch("/actions?type=mass_copy_set", {method: "POST", body: package}).then (function(response) {
                if (response.status == 200) {
                    CopyMoveButton.textContent = "Paste here"
                    CopyMoveButton.style.display = "block"
                    alert("Copied files. Go to the folder where you want to paste these to then click move")
                }
                else {
                    alert("An unknown error occured")
                }
            })
        }
        MassActionMoveButton.onclick = function() {
            let paths = []
            for (let i=0; i<checked_files.length; i++) {
                paths.push(CurrentFolderPath.value + "/" + checked_files[i].split(" ").splice(1).join(" "))
            }
            const package = new FormData()
            package.append("paths", paths)
            fetch("/actions?type=mass_move_set", {method: "POST", body: package}).then (function(response) {
                if (response.status == 200) {
                    CopyMoveButton.textContent = "Move here"
                    CopyMoveButton.style.display = "block"
                    alert("Copied files. Go to the folder where you want to move these to then click move")
                }
                else {
                    alert("An unknown error occured")
                }
            })
        }
        MassActionDeleteButton.onclick = function() {
            let paths = []
            for (let i=0; i<checked_files.length; i++) {
                paths.push(checked_files[i].split(" ").splice(1).join(" "))
            }
            if (confirm(`Are you sure you want to delete the following files:\\n` + paths.join(`\\n`))) {
                paths = []
                for (let i = 0; i<checked_files.length; i++) {
                    paths.push(CurrentFolderPath.value + "/" + checked_files[i].split(" ").splice(1).join(" "))
                }
                const package = new FormData()
                package.append("paths", paths)
                fetch("/actions?type=mass_delete", {method: "POST", body: package}).then (async function(response) {
                    if (response.status == 200) {
                            alert("Deleted all files / folders")
                    }
                    else {
                        alert("An unknown error occured")
                    }
                    window.location.href = "/home?path=" + encodeURIComponent(CurrentFolderPath.value)
                })
            }
        }
        FilesList.addEventListener("click", function(event) {
            let div = event.target.closest("div")
            if (window.getComputedStyle(div).padding != "12px") {
                div = div.parentElement
            }
            const inner_div = div.children[0]
            const file_icon = inner_div.children[1].textContent
            const file_name = inner_div.textContent.replace(file_icon, "").trim()
            if (event.target.tagName == "BUTTON") {
                if (event.target.textContent == "Download") {
                    const package = new FormData()
                    package.append("path", CurrentFolderPath.value + "/" + file_name)
                    fetch("/actions?type=download", {method: "POST", body: package}).then (function(response) {
                        if (response.status == 200) {
                            const new_package = document.createElement("form")
                            new_package.method = "POST"
                            new_package.action = "/actions?type=download"
                            const path = document.createElement("input")
                            path.name = "path"
                            path.value = CurrentFolderPath.value + "/" + file_name
                            new_package.appendChild(path)
                            document.body.appendChild(new_package)
                            new_package.submit()
                            document.body.removeChild(new_package)
                        }
                        else {
                            alert("An unknown error occured")
                        }
                    })
                }
                else if (event.target.textContent == "Rename") {
                    const new_name = prompt(`Enter the new name (include file extension)\\nCurrent name: ${file_name}`)
                    if (new_name) {
                        const package = new FormData()
                        package.append("path", CurrentFolderPath.value + "/" + file_name)
                        package.append("new_name", new_name)
                        fetch("/actions?type=rename", {method: "POST", body: package}).then (function(response) {
                            if (response.status == 200) {
                            }
                            else {
                                alert("An unknown error occured")
                            }
                            window.location.href = "/home?path=" + encodeURIComponent(CurrentFolderPath.value)
                        })
                    }
                }
                else if (event.target.textContent == "Copy") {
                    const package = new FormData()
                    package.append("path", CurrentFolderPath.value + "/" + file_name)
                    fetch("/actions?type=copy_set", {method: "POST", body: package}).then (function(response) {
                        if (response.status == 200) {
                            CopyMoveButton.textContent = "Paste here"
                            CopyMoveButton.style.display = "block"
                            alert("Copied " + file_name + ". Go to the folder where you want to copy this to then click paste")
                        }
                        else {
                            alert("An unknown error occured")
                        }
                    })
                }
                else if (event.target.textContent == "Move") {
                    const package = new FormData()
                    package.append("path", CurrentFolderPath.value + "/" + file_name)
                    fetch("/actions?type=move_set", {method: "POST", body: package}).then (function(response) {
                        if (response.status == 200) {
                            CopyMoveButton.textContent = "Move here"
                            CopyMoveButton.style.display = "block"
                            alert("Copied " + file_name + ". Go to the folder where you want to move this to then click move")
                        }
                        else {
                            alert("An unknown error occured")
                        }
                    })
                }
                else if (event.target.textContent == "Delete") {
                    if (confirm("Do you want to delete " + file_name)) {
                        const package = new FormData()
                        package.append("path", CurrentFolderPath.value + "/" + file_name)
                        fetch("/actions?type=delete", {method: "POST", body: package}).then (function(response) {
                            if (response.status == 200) {
                            }
                            else {
                                alert("An unknown error occured")
                            }
                            window.location.href = "/home?path=" + encodeURIComponent(CurrentFolderPath.value)
                        })
                    }
                }
            }
            else if (!(event.target.tagName == "INPUT" && event.target.type == "checkbox")) {
                if (file_icon == "📁") {
                    if (!CurrentFolderPath.value.endsWith("/")) {
                        CurrentFolderPath.value = CurrentFolderPath.value + "/"
                    }
                    window.location.href = "/home?path=" + encodeURIComponent(CurrentFolderPath.value + file_name)
                }
            }
        })
    </script>
</html>"""
                            home_html = home_html.replace("CurrentFolderPathFromPython", path)
                            if "source_path" in session:
                                home_html = home_html.replace("DisplayFromPython", "block")
                                if session["source_path"].startswith("Copy"):
                                    home_html = home_html.replace("Text1FromPython", "Paste here")
                                else:
                                    home_html = home_html.replace("Text1FromPython", "Move here")
                            else:
                                home_html = home_html.replace("DisplayFromPython", "none")
                            current_folder_path = data_folder_path + "/" + user_email + "/Data" + path
                            used_space_in_bytes = json_data["used_space_in_bytes"]
                            allocated_space_in_bytes = json_data["allocated_space_in_bytes"]
                            used_space = FormatedSize(used_space_in_bytes)
                            allocated_space = FormatedSize(allocated_space_in_bytes)
                            home_html = home_html.replace("Text2FromPython", f"Storage usage: {used_space} out of {allocated_space} used ({(used_space_in_bytes/json_data["allocated_space_in_bytes"])*100:.2f}%)")
                            home_html = home_html.replace("RemainingSpaceInBytesFromPython", str(allocated_space_in_bytes - used_space_in_bytes))
                            try:
                                folder_contents = os.listdir(current_folder_path)
                            except:
                                error_message = """<div style="display: flex; justify-content: center; align-items: center; height: 485px">
    <div style="background-color: #fee2e2; color: #b91c1c; padding: 20px 30px; border-radius: 8px; font-size: 18px; font-weight: bold; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1)">Error while viewing contents of folder</div>
</div>"""
                                home_html = home_html.replace("FilesFromFolderFromPython", error_message)
                                return home_html
                            if len(folder_contents) == 0:
                                empty_folder_message = """<div style="display: flex; justify-content: center; align-items: center; height: 485px">
    <div style="background-color: #f9fafb; color: #374151; padding: 20px 30px; border-radius: 8px; font-size: 18px; font-weight: bold; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1)">Empty folder</div>
</div>"""
                                home_html = home_html.replace("FilesFromFolderFromPython", empty_folder_message)
                                return home_html
                            file_elements = ""
                            folders = []
                            files = []
                            for item in folder_contents:
                                if os.path.isdir(current_folder_path + "/" + item):
                                    folders.append(item)
                                else:
                                    files.append(item)
                            folder_contents = natsorted(folders) + natsorted(files)
                            for item in folder_contents:
                                if os.path.isdir(current_folder_path + "/" + item):
                                    file_elements += f"""<file icon="📁" name="{item}" last_modified="-" size="-"></file>\n"""
                                else:
                                    file_extension = item.split(".")[-1].lower()
                                    if file_extension in ["txt", "pdf", "doc", "py", "js", "html", "java"]:
                                        file_icon="📄"
                                    elif file_extension in ["png", "jpg", "jpeg", "gif"]:
                                        file_icon="📷"
                                    elif file_extension in ["exe", "msi"]:
                                        file_icon = "⚙️"
                                    elif file_extension in ["mp4", "mkv", "avi"]:
                                        file_icon="🎬"
                                    elif file_extension in ["mp3", "wav", "flac"]:
                                        file_icon="🎵"
                                    elif file_extension == "lnk":
                                        file_icon = "🔗"
                                    elif file_extension in ["zip",  "rar",  "7z",  "tar",  "gz"]:
                                        file_icon = "🔒"
                                    else:
                                        file_icon="❓"
                                    last_modified = datetime.fromtimestamp(os.path.getmtime(f"{current_folder_path}/{item}")).strftime("%d-%m-%Y %I:%M %p")
                                    file_elements += f"""<file icon="{file_icon}" name="{item}" last_modified="{last_modified}" size="{FormatedSize(os.path.getsize(f"{current_folder_path}/{item}"))}"></file>\n"""
                            home_html = home_html.replace("FilesFromFolderFromPython", file_elements)
                            return home_html
    else:
        try:
            user_email = session["login_data"][0]
            session_id = session["login_data"][1]
            json_file = open(data_folder_path + "/" + user_email + "/info.json", "r")
            json_data = json.load(json_file)
            json_file.close()
            if json_data["session_id"] == session_id:
                path = data_folder_path + "/" + user_email + "/Data" + request.args.get("path")
                total_upload_size_in_bytes = 0
                for file in request.files.getlist("Files"):
                    file.seek(0, os.SEEK_END)
                    total_upload_size_in_bytes += file.tell()
                    file.seek(0)
                if total_upload_size_in_bytes <= json_data["allocated_space_in_bytes"] - json_data["used_space_in_bytes"]:
                    json_data["used_space_in_bytes"] += total_upload_size_in_bytes
                    json_file = open(data_folder_path + "/" + user_email + "/info.json", "w")
                    json.dump(json_data, json_file, indent=4)
                    json_file.close()
                    for f in request.files.getlist("Files"):
                        os.makedirs(os.path.dirname(f"{path}/{f.filename}"), exist_ok=True)
                        f.save(f"{path}/{f.filename}")
                    return ""
                else:
                    return "", 301
            else:
                return "", 300
        except:
            return "", 300
@app.route("/account_settings", methods=["GET", "POST"])
def account_settings():
    if request.method == "GET":
        if not "login_data" in session:
            return redirect("/login")
        else:
            user_email = session["login_data"][0]
            if not os.path.exists(data_folder_path + "/" + user_email):
                session.clear()
                return account_not_found.replace("user_email", user_email)
            else:
                json_file = open(data_folder_path + "/" + user_email + "/info.json")
                json_data = json.load(json_file)
                json_file.close()
                if json_data["session_id"] != session["login_data"][1]:
                    session.clear()
                    return invalid_session
                else:
                    if not (json_data["admin_verified"] and json_data["allocated_space_in_bytes"] is not None):
                        return awaiting_verification
                    else:
                        account_settings_html = """<!DOCTYPE html>
<html>
    <head>
        <title>Custom Cloud Storage</title>
    </head>
    <body style="font-family: Arial; margin: 0; background-color: #f5f6fa">
        <header style="font-size: 24px; background-color: #1f2937; color: white; font-weight: bold; padding: 16px 32px">Custom Cloud Storage</header>
        <button id="back" style="position: absolute; padding: 10px; background-color: #3b82f6; color: white; border: none; border-radius: 15px; width: 100px; font-size: 15px; top: 100px; left: 40px" onmouseover="this.style.background='#2563eb'" onmouseout="this.style.background='#3b82f6'">Back</button>
        <div id="OptionsContainer" style="display: flex; justify-content: center; align-items: center; flex-direction: column; margin: 30px 0px 0px 0px">
            <div style="background-color: white; width: 460px; padding: 20px; box-shadow: -4px 4px 10px rgba(0, 0, 0, 0.1); border: 0px; border-radius: 8px; margin: 0px 0px 20px 0px">
                <h3 style="margin: 0px 0px 20px 0px">Account information</h3>
                <p style="margin: 0px 0px 10px 0px"><span style="font-weight: bold">Current email: </span><span style="color: #555">""" + user_email + """</span></p>
                <p style="margin: 0px"><span style="font-weight: bold">Account created at: </span><span style="color: #555">""" + json_data["created_at"] + """</span></p>
            </div>
            <div style="background-color: white; width: 460px; padding: 20px; box-shadow: -4px 4px 10px rgba(0, 0, 0, 0.1); border: 0px; border-radius: 8px; margin: 0px 0px 20px 0px">
                <h3 style="margin: 0px 0px 20px 0px">Change Password</h3>
                <form id="DataForm1" style="width: 100%">
                    <input type="password" placeholder="Enter your current password" id="CurrentPassword" required style="width: 100%; border: 1px solid #ccc; border-radius: 5px; padding: 10px; box-sizing: border-box; margin: 0px 0px 10px 0px">
                    <input type="password" placeholder="Enter your new password" id="NewPassword" required style="width: 100%; border: 1px solid #ccc; border-radius: 5px; padding: 10px; box-sizing: border-box; margin: 0px 0px 10px 0px">
                    <input type="password" placeholder="Confirm your new password" id="ConfirmNewPassword" required style="width: 100%; border: 1px solid #ccc; border-radius: 5px; padding: 10px; box-sizing: border-box; margin: 0px 0px 10px 0px">
                    <button style="padding: 10px; background-color: #3b82f6; border: none; border-radius: 5px; color: white; width: 100%; cursor: pointer" onmouseover="this.style.background='#2563eb'" onmouseout="this.style.background='#3b82f6'">Change Password</button>
                </form>
            </div>
            <div style="background-color: white; width: 460px; padding: 20px; box-shadow: -4px 4px 10px rgba(0, 0, 0, 0.1); border: 0px; border-radius: 8px">
                <button id="ChangeEmail" style="padding: 10px; background-color: #3b82f6; border: none; border-radius: 5px; color: white; width: 100%; cursor: pointer; margin: 0px 0px 10px 0px" onmouseover="this.style.background='#2563eb'" onmouseout="this.style.background='#3b82f6'">Change Email</button>
                <button id="logout" style="padding: 10px; background-color: #3b82f6; border: none; border-radius: 5px; color: white; width: 100%; cursor: pointer; margin: 0px 0px 10px 0px" onmouseover="this.style.background='#2563eb'" onmouseout="this.style.background='#3b82f6'">Log Out</button>
                <button id="DeleteAccount" style="padding: 10px; background-color: #ef4444; border: none; border-radius: 5px; color: white; width: 100%; cursor: pointer" onmouseover="this.style.background='#dc2626'" onmouseout="this.style.background='#ef4444'">Delete Account</button>
            </div>
        </div>
    </body>
    <script>
        const back = document.getElementById("back")
        const OptionsContainer = document.getElementById("OptionsContainer")
        const DataForm1 = document.getElementById("DataForm1")
        const CurrentPassword = document.getElementById("CurrentPassword")
        const NewPassword = document.getElementById("NewPassword")
        const ConfirmNewPassword = document.getElementById("ConfirmNewPassword")
        const ChangeEmail = document.getElementById("ChangeEmail")
        const logout = document.getElementById("logout")
        const DeleteAccount = document.getElementById("DeleteAccount")
        function EnableForm(form) {
            for (let element of form.elements) {
                element.disabled = false
            }
        }
        function DisableForm(form) {
            for (let element of form.elements) {
                element.disabled = true
            }
        }
        back.onclick = function() {
            window.location.href = "/home?path=/"
        }
        DataForm1.addEventListener("submit", function(event) {
            event.preventDefault()
            DisableForm(DataForm1)
            if (NewPassword.value != ConfirmNewPassword.value) {
                alert("New passwords do not match")
                EnableForm(DataForm1)
            }
            else if (NewPassword.value.length < 5) {
                alert("New password must be atleast 5 characters long")
                EnableForm(DataForm1)
            }
            else {
                const package = new FormData()
                package.append("password", CurrentPassword.value)
                package.append("new_password", NewPassword.value)
                fetch("/account_settings", {method: "POST", body: package}).then(function(response) {
                    if (response.status == 200) {
                        alert("Password changed successfully")
                    }
                    else if (response.status == 301) {
                        alert("Incorrect password")
                    }
                    else if (response.status == 302) {
                        alert("New password must be atleast 5 characters long")
                    }
                    else {
                        alert("An unknown error occured")
                    }
                    EnableForm(DataForm1)
                })
            }
        })
        ChangeEmail.onclick = function() {
            window.location.href = "/change_email"
        }
        logout.onclick = function () {
            fetch("/logout", {method: "POST"}).then(function(response) {
                if (response.status == 200) {
                    alert("Successfully logged out")
                    window.location.href = "/login"
                }
                else {
                    alert("An unknown error occured")
                }
            })
        }
        DeleteAccount.onclick = function() {
            window.location.href = "/delete_account"
        }
    </script>
</html>"""
                        return account_settings_html
    else:
        try:
            user_email = session["login_data"][0]
            session_id = session["login_data"][1]
            hashed_password = sha256(request.form.get("password").encode()).hexdigest()
            hashed_new_password = sha256(request.form.get("new_password").encode()).hexdigest()
            json_file = open(data_folder_path + "/" + user_email + "/info.json", "r")
            json_data = json.load(json_file)
            json_file.close()
            if session_id == json_data["session_id"]:
                hashed_password = sha256(request.form.get("password").encode()).hexdigest()
                if hashed_password == json_data["hashed_password"]:
                    new_password = request.form.get("new_password")
                    if len(new_password) < 5:
                        return "", 302
                    else:
                        hashed_new_password = sha256(new_password.encode()).hexdigest()
                        json_data["hashed_password"] = hashed_new_password
                        session_id = sha256((user_email+hashed_new_password).encode()).hexdigest()
                        json_data["session_id"] = session_id
                        json_file = open(data_folder_path + "/" + user_email + "/info.json", "w")
                        json.dump(json_data, json_file, indent=4)
                        json_file.close()
                        session["login_data"] = [user_email, session_id]
                        return ""
                else:
                    return "", 301
            else:
                return "", 300
        except:
            return "", 300
@app.route("/change_email", methods=["GET", "POST"])
def change_email():
    if request.method == "GET":
        if not "login_data" in session:
            return redirect("/login")
        else:
            user_email = session["login_data"][0]
            if not os.path.exists(data_folder_path + "/" + user_email):
                session.clear()
                return account_not_found.replace("user_email", user_email)
            else:
                json_file = open(data_folder_path + "/" + user_email + "/info.json")
                json_data = json.load(json_file)
                json_file.close()
                if json_data["session_id"] != session["login_data"][1]:
                    session.clear()
                    return invalid_session
                else:
                    if not (json_data["admin_verified"] and json_data["allocated_space_in_bytes"] is not None):
                        return awaiting_verification
                    else:
                        change_email = """<!DOCTYPE html>
<html>
    <head>
        <title>Custom Cloud Storage</title>
    </head>
    <body style="font-family: Arial; margin: 0; background-color: #f5f6fa">
        <header style="font-size: 24px; background-color: #1f2937; color: white; font-weight: bold; padding: 16px 32px">Custom Cloud Storage</header>
        <button id="back" style="position: absolute; padding: 10px; background-color: #3b82f6; color: white; border: none; border-radius: 15px; width: 100px; font-size: 15px; top: 100px; left: 40px">Back</button>
        <div id="VerificationContainer1" style="height: calc(100vh - 60px); display: flex; justify-content: center; align-items: center">
            <div style="border-radius: 8px; background-color: white; padding: 30px; width: 400px; display: flex; align-items: center; justify-content: center; flex-direction: column; box-shadow: -4px 4px 10px rgba(0, 0, 0, 0.1)">
                <h2 style="margin-bottom: 20px">Verification Required</h2>
                <p style="text-align: center; margin-bottom: 20px; font-size: 18px; color: #555">A verification code has been sent to """ + user_email + """, please enter the code below to to proceed with the email change procedure</p>
                <form id="DataForm1" style="width: 100%">
                    <input id="VerificationCode1" placeholder="Enter the 6 digit verification code" required maxLength="6" style="width: 100%; padding: 10px; border-radius: 5px; border-width: 1px; border-color: #ccc; border-style: solid; margin-bottom: 20px; box-sizing: border-box; text-align: center">
                    <button style="padding: 10px; background-color: #3b82f6; border-radius: 5px; border: none; font-size: 15px; color: white; cursor: pointer; width: 100%">Verify</button>
                </form>
            </div>
        </div>
        <div id="EmailContainer" style="height: calc(100vh - 60px); display: none; justify-content: center; align-items: center">
            <div style="border-radius: 8px; background-color: white; padding: 30px; width: 400px; display: flex; align-items: center; justify-content: center; flex-direction: column; box-shadow: -4px 4px 10px rgba(0, 0, 0, 0.1)">
                <h2 style="margin-bottom: 20px">New Email</h2>
                <p style="text-align: center; margin-bottom: 20px; font-size: 18px; color: #555">Please enter your new email address</p>
                <form id="DataForm2" style="width: 100%">
                    <input id="NewEmail" type="email" placeholder="Enter new email address" required style="width: 100%; padding: 10px; border-radius: 5px; border-width: 1px; border-color: #ccc; border-style: solid; margin-bottom: 20px; box-sizing: border-box; text-align: center">
                    <button style="padding: 10px; background-color: #3b82f6; border-radius: 5px; border: none; font-size: 15px; color: white; cursor: pointer; width: 100%">Continue</button>
                </form>
            </div>
        </div>
        <div id="VerificationContainer2" style="height: calc(100vh - 60px); display: flex; justify-content: center; align-items: center">
            <div style="border-radius: 8px; background-color: white; padding: 30px; width: 400px; display: flex; align-items: center; justify-content: center; flex-direction: column; box-shadow: -4px 4px 10px rgba(0, 0, 0, 0.1)">
                <h2 style="margin-bottom: 20px">Verification Required</h2>
                <p id="VerificationMessage" style="text-align: center; margin-bottom: 20px; font-size: 18px; color: #555"></p>
                <form id="DataForm3" style="width: 100%">
                    <input id="VerificationCode2" placeholder="Enter the 6 digit verification code" required maxLength="6" style="width: 100%; padding: 10px; border-radius: 5px; border-width: 1px; border-color: #ccc; border-style: solid; margin-bottom: 20px; box-sizing: border-box; text-align: center">
                    <button style="padding: 10px; background-color: #3b82f6; border-radius: 5px; border: none; font-size: 15px; color: white; cursor: pointer; width: 100%">Change Email</button>
                </form>
            </div>
        </div>
    </body>
    <script>
        const back = document.getElementById("back")
        const VerificationContainer1 = document.getElementById("VerificationContainer1")
        const DataForm1 = document.getElementById("DataForm1")
        const VerificationCode1 = document.getElementById("VerificationCode1")
        const EmailContainer = document.getElementById("EmailContainer")
        const DataForm2 = document.getElementById("DataForm2")
        const NewEmail = document.getElementById("NewEmail")
        const VerificationContainer2 = document.getElementById("VerificationContainer2")
        const VerificationMessage = document.getElementById("VerificationMessage")
        const VerificationCode2 = document.getElementById("VerificationCode2")
        function VerifyVerificationCodeFormat(verification_code) {
            for (let i=0; i<verification_code.length; i++) {
                if (verification_code[i] < "0" || verification_code[i] > "9") {
                    return "Please enter only numbers"
                }
            }
            if (verification_code.length != 6) {
                return "Please enter a 6 digit verification code"
            }
            return true
        }
        function EnableForm(form) {
            for (let element of form.elements) {
                element.disabled = false
            }
        }
        function DisableForm(form) {
            for (let element of form.elements) {
                element.disabled = true
            }
        }
        const package = new FormData()
        package.append("stage", "1")
        fetch("/change_email", {method: "POST", body: package}).then(function(response) {
            if (response.status != 200) {
                alert("An unknown error occured")
            }
        })
        back.onclick = function() {
            window.location.href = "/account_settings"
        }
        DataForm1.addEventListener("submit", function(event) {
            event.preventDefault()
            DisableForm(DataForm1)
            const ValidationResult = VerifyVerificationCodeFormat(VerificationCode1.value)
            if (ValidationResult == true) {
                const package = new FormData()
                package.append("stage", "2")
                package.append("verification_code", VerificationCode1.value)
                fetch("/change_email", {method: "POST", body: package}).then(function(response) {
                    if (response.status == 200) {
                        VerificationContainer1.style.display = "none"
                        EmailContainer.style.display = "flex"
                    }
                    else if (response.status == 301) {
                        alert("Incorrect verification code")
                        EnableForm(DataForm1)
                    }
                    else {
                        alert("An unknown error occured")
                        EnableForm(DataForm1)
                    }
                })
            }
            else {
                alert(ValidationResult)
                EnableForm(DataForm1)
            }
        })
        DataForm2.addEventListener("submit", function(event) {
            event.preventDefault()
            DisableForm(DataForm2)
            const package = new FormData()
            package.append("stage", "3")
            package.append("new_email", NewEmail.value)
            fetch("/change_email", {method: "POST", body: package}).then(function(response) {
                if (response.status == 200) {
                    EmailContainer.style.display = "none"
                    VerificationContainer2.style.display = "flex"
                    VerificationMessage.textContent = "A verification code has been sent to " + NewEmail.value + ", please enter the code below to complete the email change procedure"
                }
                else if (response.status == 301) {
                    alert("This email is already under use")
                    EnableForm(DataForm2)
                }
                else {
                    alert("An unknown error occured")
                    EnableForm(DataForm2)
                }
            })
        })
        DataForm3.addEventListener("submit", function(event) {
            event.preventDefault()
            DisableForm(DataForm3)
            const ValidationResult = VerifyVerificationCodeFormat(VerificationCode2.value)
            if (ValidationResult == true) {
                const package = new FormData()
                package.append("stage", "4")
                package.append("new_email", NewEmail.value)
                package.append("verification_code", VerificationCode2.value)
                fetch("/change_email", {method: "POST", body: package}).then(function(response) {
                    if (response.status == 200) {
                        alert("Your email has been changed successfully")
                        window.location.href = "/account_settings"
                    }
                    else if (response.status == 301) {
                        alert("Incorrect verification code")
                        EnableForm(DataForm3)
                    }
                    else {
                        alert("An unknown error occured")
                        EnableForm(DataForm3)
                    }
                })
            }
            else {
                alert(ValidationResult)
                Enable(DataForm3)
            }
        })
    </script>
</html>"""
                        return change_email
    else:
        try:
            user_email = session["login_data"][0]
            session_id = session["login_data"][1]
            json_file = open(data_folder_path + "/" + user_email + "/info.json", "r")
            json_data = json.load(json_file)
            json_file.close()
            if json_data["session_id"] == session_id:
                stage = request.form.get("stage")
                if stage == "1":
                    verification_code = str(random.randint(100000, 999999))
                    if not os.path.exists(data_folder_path + "/Change Email 1/" + user_email):
                        os.mkdir(data_folder_path + "/Change Email 1/" + user_email)
                    json_file = open(data_folder_path + "/Change Email 1/" + user_email + "/info.json", "w")
                    json.dump({"verification_code": verification_code, "completed": False}, json_file, indent=4)
                    json_file.close()
                    html_content = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background-color: #f5f6fa; margin: 0px; display: flex; justify-content: center">
    <div style="width: 100%; background-color: #fff; padding: 30px; border-radius: 12px; box-shadow: -4px 4px 10px rgba(0, 0, 0, 0.1); text-align: center">
        <h2 style="color: #1f2937">Email Change</h2>
        <p style="font-size: 16px; color: #555">Hello! To proceeded with your email change procedure please use the verification code below</p>
        <p style="font-size: 22px; font-weight: bold; margin: 20px; letter-spacing: 4px; color: #3b82f6">{verification_code}</p>
    </div>
</body>
</html>"""
                    SendEmail(user_email, html_content)
                    return ""
                elif stage == "2":
                    verification_code = request.form.get("verification_code")
                    json_file = open(data_folder_path + "/Change Email 1/" + user_email + "/info.json", "r")
                    json_data = json.load(json_file)
                    json_file.close()
                    if json_data["verification_code"] == verification_code:
                        json_file = open(data_folder_path + "/Change Email 1/" + user_email + "/info.json", "w")
                        json_data["completed"] = True
                        json.dump(json_data, json_file, indent=4)
                        json_file.close()
                        return "", 200
                    else:
                        return "", 301
                elif stage == "3":
                    json_file = open(data_folder_path + "/Change Email 1/" + user_email + "/info.json", "r")
                    json_data = json.load(json_file)
                    json_file.close()
                    if json_data["completed"]:
                        new_email = request.form.get("new_email")
                        if os.path.exists(data_folder_path + "/" + new_email):
                            return "", 301
                        else:
                            verification_code = str(random.randint(100000, 999999))
                            if not os.path.exists(data_folder_path + "/Change Email 2/" + new_email):
                                os.mkdir(data_folder_path + "/Change Email 2/" + new_email)
                            json_file = open(data_folder_path + "/Change Email 2/" + new_email + "/info.json", "w")
                            json.dump({"verification_code": verification_code}, json_file, indent=4)
                            json_file.close()
                            html_content = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background-color: #f5f6fa; margin: 0px; display: flex; justify-content: center">
    <div style="width: 100%; background-color: #fff; padding: 30px; border-radius: 12px; box-shadow: -4px 4px 10px rgba(0, 0, 0, 0.1); text-align: center">
        <h2 style="color: #1f2937">Verify Your Email</h2>
        <p style="font-size: 16px; color: #555">Hello! A request was made to change the email address linked to a Custom Cloud Storage account from <span style="font-weight: bold">{user_email}</span> to this address. To proceed with the email change procedure please use the verification code below</p>
        <p style="font-size: 22px; font-weight: bold; margin: 20px; letter-spacing: 4px; color: #3b82f6">{verification_code}</p>
    </div>
</body>
</html>"""
                            SendEmail(new_email, html_content)
                            return "", 200
                    else:
                        return "", 300
                elif stage == "4":
                    new_email = request.form.get("new_email")
                    verification_code = request.form.get("verification_code")
                    json_file = open(data_folder_path + "/Change Email 2/" + new_email + "/info.json", "r")
                    json_data = json.load(json_file)
                    json_file.close()
                    if json_data["verification_code"] == verification_code:
                        json_file = open(data_folder_path + "/" + user_email + "/info.json", "r")
                        json_data = json.load(json_file)
                        json_file.close()
                        session_id = sha256((new_email+json_data["hashed_password"]).encode()).hexdigest()
                        json_data["session_id"] = session_id
                        json_file = open(data_folder_path + "/" + user_email + "/info.json", "w")
                        json.dump(json_data, json_file, indent=4)
                        json_file.close()
                        os.rename(data_folder_path + "/" + user_email, data_folder_path + "/" + new_email)
                        shutil.rmtree(data_folder_path + "/Change Email 1/" + user_email)
                        shutil.rmtree(data_folder_path + "/Change Email 2/" + new_email)
                        html_content = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background-color: #f5f6fa; margin: 0px; display: flex; justify-content: center">
    <div style="width: 100%; background-color: #fff; padding: 30px; border-radius: 12px; box-shadow: -4px 4px 10px rgba(0, 0, 0, 0.1); text-align: center">
        <h2 style="color: #1f2937">Email Change</h2>
        <p style="font-size: 16px; color: #555">Your Custom Cloud Storage account's email has been changed from <span style="font-weight: bold">{user_email}</span> to <span style="font-weight: bold">{new_email}</span>. From now on, you can no longer access your account from this email ({user_email})</p>
    </div>
</body>
</html>"""
                        SendEmail(user_email, html_content)
                        html_content = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background-color: #f5f6fa; margin: 0px; display: flex; justify-content: center">
    <div style="width: 100%; background-color: #fff; padding: 30px; border-radius: 12px; box-shadow: -4px 4px 10px rgba(0, 0, 0, 0.1); text-align: center">
        <h2 style="color: #1f2937">Email Change</h2>
        <p style="font-size: 16px; color: #555">A Custom Cloud Storage account's email has been changed from <span style="font-weight: bold">{user_email}</span> to <span style="font-weight: bold">{new_email}</span>. You can now access this account using this email ({new_email})</p>
    </div>
</body>
</html>"""
                        SendEmail(new_email, html_content)
                        session["login_data"] = [new_email, session_id]
                        return "", 200
                    else:
                        return "", 301
                else:
                    return "", 300
            else:
                return "", 300
        except:
            return "", 300
@app.route("/logout", methods=["POST"])
def logout():
    try:
        session.clear()
        return ""
    except:
        return "", 300
@app.route("/delete_account", methods=["GET", "POST"])
def delete_account():
    if request.method == "GET":
        if not "login_data" in session:
            return redirect("/login")
        else:
            user_email = session["login_data"][0]
            if not os.path.exists(data_folder_path + "/" + user_email):
                session.clear()
                return account_not_found.replace("user_email", user_email)
            else:
                json_file = open(data_folder_path + "/" + user_email + "/info.json")
                json_data = json.load(json_file)
                json_file.close()
                if json_data["session_id"] != session["login_data"][1]:
                    session.clear()
                    return invalid_session
                else:
                    if not (json_data["admin_verified"] and json_data["allocated_space_in_bytes"] is not None):
                        return awaiting_verification
                    else:
                        delete_account_html = """<!DOCTYPE html>
<html>
        <head>
            <title>Custom Cloud Storage</title>
        </head>
        <body style="font-family: Arial; margin: 0; background-color: #f5f6fa">
            <header style="font-size: 24px; background-color: #1f2937; color: white; font-weight: bold; padding: 16px 32px">Custom Cloud Storage</header>
            <button id="back" style="position: absolute; padding: 10px; background-color: #3b82f6; color: white; border: none; border-radius: 15px; width: 100px; font-size: 15px; top: 100px; left: 40px">Back</button>
            <div id="DeleteAccountContainer" style="height: calc(100vh - 60px); display: flex; justify-content: center; align-items: center">
                <div style="border-radius: 8px; background-color: white; padding: 30px; width: 400px; display: flex; align-items: center; justify-content: center; flex-direction: column; box-shadow: -4px 4px 10px rgba(0, 0, 0, 0.1)">
                    <h2 style="margin-bottom: 20px">Delete Account</h2>
                    <p id="VerificationMessage" style="text-align: center; margin-bottom: 20px; font-size: 18px; color: #555">Deleting your account will also delete all of your files. Please enter your password if you still wish to delete your account</p>
                    <form id="DataForm" style="width: 100%">
                        <input id="password" type="password" name="password" placeholder="Enter your password" required style="width: 100%; padding: 10px; border-radius: 5px; border-width: 1px; border-color: #ccc; border-style: solid; margin-bottom: 20px; box-sizing: border-box">
                        <button id="SubmitButton" style="padding: 10px; background-color: #ef4444; border-radius: 5px; border: none; font-size: 15px; color: white; cursor: pointer; width: 100%; margin-bottom: 5px">Delete Account</button>
                    </form>
                </div>
            </div>
        </body>
        <script>
            const back = document.getElementById("back")
            const DataForm = document.getElementById("DataForm")
            const password = document.getElementById("password")
            function EnableForm(form) {
                for (let element of form.elements) {
                    element.disabled = false
                }
            }
            function DisableForm(form) {
                for (let element of form.elements) {
                    element.disabled = true
                }
            }
            back.onclick = function() {
                window.location.href = "/account_settings"
            }
            DataForm.addEventListener("submit", function(event) {
                event.preventDefault()
                DisableForm(DataForm)
                const package = new FormData()
                package.append("password", password.value)
                fetch("/delete_account", {method: "POST", body: package}).then(function(response) {
                    if (response.status == 200) {
                        alert("You account has been successfully deleted")
                        window.location.href = "/login"
                    }
                    else if (response.status == 301) {
                        alert("Incorrect password")
                        password.value = ""
                        EnableForm(DataForm)
                    }
                    else {
                        alert("An unknown error occured")
                        EnableForm(DataForm)
                    }
                })
            })
        </script>
    </html>"""
                        return delete_account_html
    else:
        try:
            user_email = session["login_data"][0]
            session_id = session["login_data"][1]
            hashed_password = sha256(request.form.get("password").encode()).hexdigest()
            json_file = open(data_folder_path + "/" + user_email + "/info.json", "r")
            json_data = json.load(json_file)
            json_file.close()
            if session_id == json_data["session_id"]:
                if hashed_password == json_data["hashed_password"]:
                    shutil.rmtree(data_folder_path + "/" + user_email)
                    session.clear()
                    return ""
                else:
                    return "", 301
            else:
                return "", 300
        except:
            return "", 300
app.run(host="0.0.0.0", port=5003)