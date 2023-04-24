import subprocess

import colors
import os
import json
from subprocess import check_output

config_file_name = 'config.json'


def check_input(message):
    while True:
        answer = input(message)
        if len(answer.split(' ')) > 1:
            print(f"{colors.red_print_color}Cannot have spaces{colors.reset_print_color}")
            continue
        return answer


def check_yes_no(message):
    print(message)
    if message == '':
        return False
    if 'y' in message[0:1].lower():
        return True

    return False


def find_docker():
    result = None

    while not result:
        format_option = ' --format "{{.Names}}"'
        container_list = check_output(f"docker ps -a{format_option}", shell=True).decode().split('\n')
        # remove empty string
        del container_list[-1]
        print(f"{colors.blue_print_color}Available containers:{colors.green_print_color}")
        # show all containers
        for container_name in container_list:
            print(
                f"      {colors.blue_print_color}{container_list.index(container_name) + 1}{colors.green_print_color} - {container_name}{colors.reset_print_color}")

        try:
            id = int(input('Write container number: '))

            if id > len(container_list):
                raise AttributeError
        except Exception as error:
            if isinstance(error, ValueError):
                print(f'{colors.red_print_color}Should be integer!{colors.reset_print_color}')
            else:
                print(f"{colors.red_print_color}Should be in list!{colors.reset_print_color}")
            continue

        result = container_list.__getitem__(id - 1)

    return result


def is_container_run(container_name: str):
    format_option = ' --format "{{.Names}}"'
    return check_output(f"docker ps {format_option} --filter name={container_name.lower()}", shell=True) \
        .decode() \
        .replace('\n', '')


def find_dump():
    result = None
    while not result:
        path = check_input("Write path to dump file: ")
        if not os.path.isfile(path):
            print(f"{colors.red_print_color}No such file or directory!{colors.reset_print_color}")
            continue
        result = path

    return result


def write_db_info():
    return {
        "dbName": check_input('Write db name: '),
        "dbUser": check_input('Write db username: '),
    }


def get_config():
    if not os.path.isfile(config_file_name):
        with open(config_file_name, 'w') as file:
            file.write(json.dumps({}))
        return dict()

    with open(config_file_name) as file:
        return json.load(file)


def rewrite_config(data: json):
    with open(config_file_name, 'w') as f:
        f.write(json.dumps(data, indent=2))


def write_new_data_to_config():
    config = get_config()

    if not config.get('containerName') or check_yes_no(check_input(
            f"Change container name?(now: {colors.green_print_color}{config.get('containerName')}{colors.reset_print_color}): {colors.reset_print_color}")):
        config['containerName'] = find_docker()
        rewrite_config(config)

    if not config.get('dumpPath') or check_yes_no(check_input(
            f"Change dump path?(now: {colors.green_print_color}{config.get('dumpPath')}{colors.reset_print_color}): {colors.reset_print_color}")):
        config['dumpPath'] = find_dump()
        rewrite_config(config)

    if not config.get('db') or check_yes_no(check_input(
            f"Change db info?(now: {colors.green_print_color}{config.get('db')}{colors.reset_print_color}): {colors.reset_print_color}")):
        config['db'] = write_db_info()
        rewrite_config(config)


def stop_postgres():
    try:
        postgres_status = subprocess.check_output('systemctl is-active postgresql', shell=True).decode()
    except Exception as error:
        print(error)
        postgres_status = 'inactive'

    if postgres_status.__eq__('active'):
        print(f'{colors.blue_print_color}Stopping postgres service...{colors.reset_print_color}')
        subprocess.check_output('systemctl stop postgresql', shell=True)


def add_role():
    config = get_config()
    container_name = config.get('containerName')
    # todo change
    db_user = config['db']['dbUser']
    db_name = config['db']['dbName']

    if is_container_run(container_name) != container_name:
        stop_postgres()
        try:
            print(subprocess.check_output(f"docker start {container_name}", shell=True).decode())
        except Exception as error:
            print(error)
            print('Something wrong when starting docker')

    roles = subprocess.check_output(
        f"docker exec -i {container_name} psql -U {db_user} {db_name} -t -c \"SELECT rolname FROM pg_roles;\"",
        shell=True) \
        .decode() \
        .split('\n')

    print(
        f"{colors.blue_print_color}All roles in db [{colors.magenta_print_color}{db_name}{colors.blue_print_color}]:{colors.reset_print_color}")
    for role in roles:
        if role == '':
            continue

        if role[1:4] == 'pg_':
            print(f"      {role.strip()}")
        else:
            print(f"      {colors.green_print_color}{role.strip()}{colors.reset_print_color}")

    enough_roles = True
    while True:
        answer = check_input("add new role?: ")
        if 'y' in answer[0:1].lower():
            enough_roles = False
            break
        elif 'n' in answer[0:1].lower() or answer == '':
            break
        continue

    if not enough_roles:
        while True:
            role = check_input("Type new role: ")
            subprocess.check_output(
                f"docker exec -i {container_name} psql -U {db_user} {db_name} -t -c \"CREATE ROLE \"{role}\";\"",
                shell=True)
            one_more = check_input('One more role?: ')

            if 'y' in one_more[0:1].lower():
                continue
            elif 'n' in one_more[0:1].lower():
                break


def do_migration():
    config = get_config()
    if len(config) == 0:
        print(f"{colors.red_print_color}WRONG CONFIG{colors.reset_print_color}")
        return

    container_name = config['containerName']
    dump_path = config['dumpPath']
    db_user = config['db']['dbUser']
    db_name = config['db']['dbName']
    subprocess.run(f"docker exec -i {container_name} psql -U {db_user} {db_name} < \"{dump_path}\";",
                   shell=True,
                   stdout=subprocess.PIPE)


if __name__ == '__main__':
    write_new_data_to_config()
    add_role()
    # todo check and create db step
    do_migration()
