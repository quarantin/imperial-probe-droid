
# Use an official Python runtime as a parent image
FROM python:3.7.3

# Update the package manager cache
RUN apt-get update

# Install Nginx, uWSGI, sqlite3 and vim
RUN apt-get install --yes nginx uwsgi sqlite3 vim

# Copy our custom Nginx configuration file
COPY conf/nginx/swgoh.conf /etc/nginx/sites-enabled/

# Copy our custom uWSGI configuration file
COPY conf/uwsgi/swgoh.ini /etc/uwsgi/apps-enabled/

# Clone repository into the container at /ipd.git
RUN git clone https://github.com/quarantin/imperial-probe-droid /ipd.git

# Set the working directory to /ipd
WORKDIR /ipd.git

# Upgrade pip to latest version
RUN pip install --upgrade pip

# Install python packages specified in requirements.txt
RUN pip install -r requirements.txt

# Copy JSON configuration
COPY config.json config.json

# Create Django migrations
RUN python manage.py makemigrations

# Apply Django migrations and create database
RUN python manage.py migrate --run-syncdb

# Copy localization files to cache folder
COPY cache/Loc_* cache/

# Copy mod recommendations from Capital Games
COPY cache/mod-recos-capital-games.json cache/

# Download all static data, translations, units, gear, skills, mod recommendations, etc
RUN ./translate.py

# Restart Nginx
RUN /etc/init.d/nginx restart

# Restart uWSGI
#RUN /etc/init.d/uwsgi restart

# Run the bot
#CMD [ "./scripts/run.sh" ]

# Start shell as fallback
CMD [ "/bin/bash" ]
