FROM python:2.7

RUN apt-get update && apt-get install -y \
    gcc \
    libsasl2-dev \
    python-dev \
    libldap2-dev \
    libssl-dev

COPY . /j-ldap/

RUN python2.7 -m pip install -r /j-ldap/requirements.txt
