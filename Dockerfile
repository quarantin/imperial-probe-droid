
# Use an official Python runtime as a parent image
FROM python:3.5.2

# Set the working directory to /ipd
WORKDIR /ipd

# Copy the current directory contents into the container at /ipd
COPY . /ipd

# Upgrade pip to latest version
RUN pip install --upgrade pip

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Run run.sh when the container launches
CMD [ "./run.sh" ]
