
# Real Life Web Apps with Robyn <a id="real-life-web-apps-with-robyn"></a>

Batman was tasked with building a web application to manage the crime data in Gotham City. The application would allow the Gotham police department to store and retrieve data on criminal activities, suspects, and their locations. He decided to use the Robyn web framework to build this application efficiently and quickly.
You can find the source code for this application [here](https://github.com/sparckles/example_robyn_app).
## [](/documentation/en/example_app#installing-robyn)[Installing Robyn](/documentation/en/example_app#installing-robyn) <a id="installing-robyn"></a>

The first step was to install Robyn. Batman created a virtual environment and installed Robyn using pip.
```bash
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install robyn
```
Copy
Copied!

## [](/documentation/en/example_app#creating-a-robyn-application)[Creating a Robyn Application](/documentation/en/example_app#creating-a-robyn-application) <a id="creating-a-robyn-application"></a>

Batman wanted to create a Robyn app and was about to create an `src/app.py` before he was told that Robyn comes with a CLI tool to create a new application. He ran the following command to create a new Robyn application.
```bash
$ python -m robyn --create
```
Copy
Copied!

This, would result in the following output.
```bash
$ python3 -m robyn --create
? Directory Path: .
? Need Docker? (Y/N) Y
? Please select project type (Mongo/Postgres/Sqlalchemy/Prisma):
❯ No DB
  Sqlite
  Postgres
  MongoDB
  SqlAlchemy
  Prisma
```
Copy
Copied!

and the following directory structure.
Batman was asked a set of questions to configure the application. He chose to use the default values for most of the questions.
And he was done! The Robyn CLI created a new application with the following structure.
```bash
├── src
│   ├── app.py
├── Dockerfile
```
Copy
Copied!
[Modeling Routes](/documentation/en/example_app/modeling_routes)