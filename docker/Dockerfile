# syntax=docker/dockerfile:1
FROM ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
ENV DEBIAN_FRONTEND=noninteractive
RUN --mount=type=secret,id=proxy_ca,required=true,mode=0444 sed -i "s|http://|https://|g" /etc/apt/sources.list.d/ubuntu.sources && export APT_CONFIG=/tmp/apt-proxy.conf && printf 'Acquire::https::CaInfo "/run/secrets/proxy_ca";\n' > "$APT_CONFIG" && apt-get update && apt-get install -y --no-install-recommends ca-certificates cmake g++ make python3 file binutils && rm -rf /var/lib/apt/lists/* /tmp/apt-proxy.conf
COPY pycdc /opt/pycdc
RUN cmake -S /opt/pycdc -B /opt/pycdc/build -DCMAKE_BUILD_TYPE=Release && cmake --build /opt/pycdc/build -j2 && cmake --install /opt/pycdc/build
WORKDIR /work
CMD ["bash"]
