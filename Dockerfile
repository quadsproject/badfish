FROM quay.io/fedora/python-310:latest

USER root

RUN dnf install -y git

COPY . /badfish

WORKDIR /badfish

RUN dnf install -y gcc python3-devel
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m build
RUN python -m pip install dist/badfish-*.tar.gz

ENTRYPOINT ["badfish"]
CMD ["-v"]
