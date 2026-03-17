#!/bin/bash
echo "Install for ubuntu24.04"
wget https://www.python.org/ftp/python/3.13.3/Python-3.13.3.tgz
tar -xvf Python-3.13.3.tgz
rm Python-3.13.3.tgz
cd Python-3.13.3/
sudo apt update
sudo apt install -y make build-essential libssl-dev zlib1g-dev   libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm   libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev   libffi-dev liblzma-dev
./configure --enable-optimizations
make -j$(nproc)
make altinstall
python3.13 --version
python3.13 -m venv .e3

echo "Now activate environment. '. .venv/bin/activate'"


sudo a2enmod proxy
sudo a2enmod proxy_http
sudo systemctl restart apache2
