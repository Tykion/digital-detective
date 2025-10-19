import sys
from helper_funcs.name_search import *
from helper_funcs.ip_search import *
from helper_funcs.un_search import *

def show_help():
    help_text = """

Usage:
    python data_digger.py [options] <input>

OPTIONS:
    -n      Performs a full-name search.
    -ip     Performs an IP search.
    -un     Performs a username search.
"""
    print(help_text)

    
    """
    1. Loop over args
    2. if next arg is one of options add to count and then count the number of inputs based on count
    3. if same counts, procceed and call functions that are needed
    """


def main():
    args = sys.argv[1:]
    i = 0

    if not args:
        show_help()
        sys.exit(0)
    
    options = {
        "-n": findby_name,
        "-ip": findby_ip,
        "-un": findby_un
    }

    while i < len(args):
        opt = args[i]
        if opt in options:
            if i + 1 < len(args):
                value = args[i + 1]
                options[opt](value)
                i += 2 #skip value
            else:
                print(f"Error missing value for {opt}")
                sys.exit()
        else:
            print(f"Unknown option: {opt}")   
            show_help()
            sys.exit(1)   

if __name__ == "__main__":
    main()
    
    