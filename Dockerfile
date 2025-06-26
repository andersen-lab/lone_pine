FROM continuumio/miniconda3
LABEL MAINTAINER="Nate Matteson <natem@scripps.edu>"

# RUN git clone https://github.com/watronfire/lone_pine.git /app

# Copy local code to the container image.
ENV APP_HOME /app
ENV PYTHONUNBUFFERED True
WORKDIR /app

ADD requirements.txt .
RUN conda install -c bioconda -c conda-forge --file requirements.txt
RUN groupadd -r app && useradd -r -g app app

COPY --chown=app:app . ./
USER app

CMD exec gunicorn --bind 0.0.0.0:8080 --log-level info --workers 1 --threads 5 --timeout 120 app:server
# CMD [ "gunicorn", "--workers=1", "--threads=1", "-b 0.0.0.0:8080", "app:server"]