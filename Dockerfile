FROM continuumio/miniconda3

LABEL MAINTAINER="Nate Matteson <natem@scripps.edu>"

RUN git clone https://github.com/watronfire/lone_pine.git /app

WORKDIR "/app"

RUN conda install -c bioconda --file requirements.txt

EXPOSE 8050

CMD [ "gunicorn", "--workers=1", "--threads=1", "-b 0.0.0.0:8050", "app:server"]