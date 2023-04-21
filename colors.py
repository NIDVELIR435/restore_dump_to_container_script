green_print_color = '\x1b[32m'
blue_print_color = '\x1b[34m'
red_print_color = '\x1b[31m'
magenta_print_color = '\x1b[35m'
reset_print_color = '\x1b[0m'

def p_green(text):
    print(f"{green_print_color}{text}{reset_print_color}")


def p_blue(text):
    print(f"{blue_print_color}{text}{reset_print_color}")


def p_red(text):
    print(f"{red_print_color}{text}{reset_print_color}")