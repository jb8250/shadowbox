FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    tor \
    curl \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 9050

CMD ["tor", "-f", "/etc/tor/torrc"]
