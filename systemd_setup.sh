#!/bin/bash

user_home=$HOME
script_path=$(realpath -s ./service/synchronizer_service.py)
script_directory=$(pwd)/service

escaped_user_home=$(echo "$user_home" | sed 's/[\/&]/\\&/g')
escaped_script_path=$(echo "$script_path" | sed 's/[\/&]/\\&/g')
escaped_script_directory=$(echo "$script_directory" | sed 's/[\/&]/\\&/g')

sed -i "s/user_home/$escaped_user_home/g" ./setup/dotfiles_synchronizer.service
sed -i "s/script_path/$escaped_script_path/g" ./setup/dotfiles_synchronizer.service
sed -i "s/script_directory/$escaped_script_directory/g" ./setup/dotfiles_synchronizer.service

cp ./setup/targets.json $HOME/.config/synchronization_targets.json

cp ./setup/dotfiles_synchronizer.service $HOME/.config/systemd/user
systemctl --user daemon-reload

read -p "Do you want to enable the daemon right away? (y/n): " answer

if [ "$answer" == "y" ]; then
	systemctl --user start dotfiles_synchronizer
	systemctl --user enable dotfiles_synchronizer
elif [ "$answer" != "n" ]; then
	echo "Invalid input. Please enter 'y' or 'n'."
fi

rm -r setup systemd_setup.sh
