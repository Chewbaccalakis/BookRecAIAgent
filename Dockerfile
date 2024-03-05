#Use Python base image
FROM python:3.11

#Set directory within container to /app
WORKDIR /app

#Copy root directory to /app
COPY . .

#Install pip modules from requirements.txt
RUN pip3 install -r requirements.txt

#Run main.py
CMD ["python3", "main.py"]