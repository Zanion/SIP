FROM chukysoria/rpi-python-testing:armv6-py27

RUN apt-get update
COPY ./ /SIP/
COPY ./docker/entrypoint.sh /

ENTRYPOINT ["/entrypoint.sh"]

