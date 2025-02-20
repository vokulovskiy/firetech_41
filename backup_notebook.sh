#!/bin/sh

BACKUP_VOL=/backup/
DOCKER_VOL=/var/lib/docker/volumes/
mkdir $BACKUP_VOL
FOLDERS=$(ls $DOCKER_VOL | grep jupyterhub-user-)
echo $DOCKER_VOL$FOLDERS
if [ -z "$FOLDERS" ]; then
  echo "Папки по маске '$MASK' не найдены."
  exit 1
fi

# Перебор найденных папок и создание архивов
for FOLDER in $FOLDERS; do
  # Создание архива для каждой папки
  tar -czvf "$BACKUP_VOL$FOLDER.tar.gz" "$DOCKER_VOL$FOLDER"
  
  echo "Папка '$FOLDER' заархивирована в '$FOLDER.tar.gz'"
done

echo "Все папки заархивированы."
ls -la $BACKUP_VOL