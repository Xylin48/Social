from replit import db
import sys
import os
from time import sleep


log = False

##i should add more notes to my code
uname = input("please enter username:  ")

psw = input("please enter password:  ")
os.system("clear")


if uname and psw not in db:
  print("making new user...")
db[uname] = "name"
db[psw] = "pswrd"
if uname and psw in db:
  #code goes in here
  print("Welcome back,", uname)
  log = True
  #after this line ofc
  while log:
   i = input(">>> ")
   if i ==("clear"):
     os.system("clear")
   if i ==("book"):
     exec(open("book.py").read())
   if i ==("settings"):
     print("not ava in alpha")
     os.system("clear")
   if i==("post"):
     post = input("posts don't get saved yet - start typing post...\n")
     os.system("clear")
    
     ps = print(uname,"-",post)
     with open("test.txt", 'w') as sys.stdout:
      print(ps)
   if i==("search"):
     s = input("please enter the user you'd like to search [Keep in mind its case sensitive]: ")
     if s in db:
       print("User found", s)
     if s not in db:
       print("User not found")
if uname not in db and psw in db:
  print("Username does not match username...")

if psw not in db and uname in db: 
  print("Password does not match password...")
