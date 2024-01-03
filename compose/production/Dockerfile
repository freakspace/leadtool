# Use an official Python runtime as a parent image
FROM python:3.12.1-slim-bookworm AS app

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV FLASK_APP=app.py

# Run Gunicorn when the container launches
CMD ["gunicorn", "-b", "0.0.0.0:80", "-w", "2", "app:app"]