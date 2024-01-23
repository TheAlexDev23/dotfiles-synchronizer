#!/bin/bash

script_path=$(realpath -s ./synchronizer_service.py)
script_directory=$(pwd)

escaped_script_path=$(echo "$script_path" | sed 's/[\/&]/\\&/g')
escaped_script_directory=$(echo "$script_directory" | sed 's/[\/&]/\\&/g')

sed -i "s/script_path/$escaped_script_path/g" ./dotfiles_synchronizer.service
sed -i "s/script_directory/$escaped_script_directory/g" ./dotfiles_synchronizer.service

sudo cp ./dotfiles_synchronizer.service /etc/systemd/system/
sudo systemctl daemon-reload

read -p "Do you want to enable the daemon right away? (y/n): " answer

if [ "$answer" == "y" ]; then
	sudo systemctl start dotfiles_synchronizer
	sudo systemctl enable dotfiles_synchronizer
elif [ "$answer" != "n" ]; then
	echo "Invalid input. Please enter 'y' or 'n'."
fi
