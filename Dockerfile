FROM python:3.8
ENV PATH="/root/.local/bin:${PATH}"

# Install postgres client
RUN wget -q https://www.postgresql.org/media/keys/ACCC4CF8.asc -O - | apt-key add - && \
    echo "deb http://apt.postgresql.org/pub/repos/apt/ bullseye-pgdg main" >> /etc/apt/sources.list.d/pgdg.list && \
    apt-get update -y && \
    apt-get install -y postgresql-client-12 tzdata nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install Heroku client
RUN curl https://cli-assets.heroku.com/install.sh | sh

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add files
ADD . /app
WORKDIR /app

# Run poetry to install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install
