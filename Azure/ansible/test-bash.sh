sudo apt update
sudo apt -y dist-upgrade

sudo apt install -y default-jre

sudo apt update

echo deb http://www.apache.org/dist/cassandra/debian 311x main | sudo tee -a /etc/apt/sources.list.d/cassandra.source.list

curl https://www.apache.org/dist/cassandra/KEYS | sudo apt-key add -

sudo apt-key adv --keyserver pool.sks-keyservers.net --recv-key A278B781FE4B2BDA

sudo apt update

sudo apt -y install cassandra
