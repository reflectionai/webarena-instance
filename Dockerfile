# Use an official Python runtime as a parent image
FROM python:3.11.4-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

RUN pip install --no-cache-dir flask

# Make port 4399 available to the world outside this container
EXPOSE 4399

# Define environment variable
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=4399

# Run app.py when the container launches
CMD ["flask", "run"]

