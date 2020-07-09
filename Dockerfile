FROM python:3.8

# Install postgres client
RUN wget -q https://www.postgresql.org/media/keys/ACCC4CF8.asc -O - | apt-key add - && \
    echo "deb http://apt.postgresql.org/pub/repos/apt/ buster-pgdg main" >> /etc/apt/sources.list.d/pgdg.list && \
    apt-get update -y && \
    apt-get install -y postgresql-client-12 tzdata

# Install Heroku client
RUN curl https://cli-assets.heroku.com/install.sh | sh

# Install poetry
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python

# Add files
ADD . /app
WORKDIR /app

# Run poetry to install dependencies
RUN . $HOME/.poetry/env && \
    poetry config virtualenvs.create false && \
    poetry install
