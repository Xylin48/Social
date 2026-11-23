from replit import db
n = input("Enter your name: ")
db["name"] = n
print("Hello, " + db["name"] + "!")
if db["name"] == "":
  print("You have no name!")
  if db["name"] not in db:
    print("Welcome New User!")
