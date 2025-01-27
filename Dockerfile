# Use the official Python 3.12 image as the base image
FROM python:3.12-slim

# Set a working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Set the default command to run the script
ENTRYPOINT ["python", "migrate_table.py"]

# By default, show the help message
CMD ["--help"]
