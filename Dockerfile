FROM mambaorg/micromamba:2.3.0
LABEL MAINTAINER="Nate Matteson <natem@scripps.edu>"

# RUN git clone https://github.com/watronfire/lone_pine.git /app

# Copy local code to the container image.
ENV APP_HOME /app
ENV PYTHONUNBUFFERED True
WORKDIR /app

ADD env.yaml .
# COPY --chown=$MAMBA_USER:$MAMBA_USER env.yaml /tmp/env.yaml
RUN micromamba install -y -n base -f env.yaml && \
    micromamba clean --all --yes
# RUN groupadd -r app && useradd -r -g app app

COPY --chown=app:app . ./
USER app

CMD exec gunicorn --bind $PORT --log-level info --workers 1 --threads 5 --timeout 120 app:server
# CMD [ "gunicorn", "--workers=1", "--threads=1", "-b 0.0.0.0:8080", "app:server"]