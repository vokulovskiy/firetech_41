##1. Установка ubuntu
Настроить сеть -> тип подключения: сетевой мост
ip a
##2. Установка ssh
sudo apt update && sudo apt upgrade
sudo apt install openssh-server
sudo systemctl enable --now ssh
sudo systemctl status ssh

sudo vi /etc/ssh/sshd_config

PasswordAuthentication = yes
PermitRootLogin = no
PubkeyAuthentication = yes

sudo service ssh restart

mkdir ~/.ssh
chmod 0700 ~/.ssh
touch ~/.ssh/authorized_keys
chmod 0644 ~/.ssh/authorized_keys

##3. Установка docker
1. Обновляем индексы пакетов apt
sudo apt update

2. Устанавливаем дополнительные пакеты
sudo apt install curl software-properties-common ca-certificates apt-transport-https -y

3. Импортируем GPG-ключ
wget -O- https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor | sudo tee /etc/apt/keyrings/docker.gpg > /dev/null

4. Добавляем репозиторий докера
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu jammy stable"| sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
5. В очередной раз обновляем индексы пакетов
sudo apt update

6. Проверяем репозиторий
apt-cache policy docker-ce

7. Устанавливаем докер
 
sudo apt install docker-ce -y
sudo systemctl status docker
sudo usermod -aG docker $USER && newgrp docker
su - uuser
id -nG

8. Устанавливаем docker-compose
sudo apt-get install docker-compose -y

docker run hello-world
docker ps

