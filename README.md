# Overview

digital-detective/data_digger CLI is built for searching many API's for information about an individual, their personal information, IP address info and their existence on social medias by providing their username.

## Prerequisites
* python3
* Internet access :)

## Installation 

1. Clone the repository and open it
```bash
git clone https://github.com/Tykion/digital-detective.git

cd digital-detective
```

2. Create a virtual environment (.venv) for dependencies

```bash
python -m venv .venv
```

3. After creating a virtual environment reopenthe terminal, you should see (.venv)

4. Install dependencies
```bash
pip install -r requirements.txt
```

5. Now create an ".env" file in the root and inside it declare a user agent
```bash
USER_AGENT={Any way the api can know who you are}
or
USER_AGENT=https://github.com/Tykion/digital-detective.git
```
6. Now that the setup is done we can run the CLI tool
```bash
cd data_digger

$ python data_digger.py --help

Usage:
    python data_digger.py [options] <input>

OPTIONS:
    -n      Performs a full-name search.
    -ip     Performs an IP search.
    -un     Performs a username search.
```

## Features
* Name search:
```bash
$ python data_digger.py -n "Dwight Schrute"

    First name: Dwight (src: 3)
    Last name: Schrute (src: 3)
    Address: Rural Rt. 6, Honesdale, PA 18431 (src: 1)
    Phone number: 7175550177 (src: 1)
    Description: fictional character in NBC's The Office (src: 1)
    Results written to file: n_dwight_schrute.txt
```

* IP Search:
```bash
$ python data_digger.py -ip "8.8.8.8"

    IP: 8.8.8.8
    ISP: AS15169 Google LLC
    Location: source1: 37.4056,-122.0775 / source2: 39.03,-77.5 / source3: 37.3860517,-122.0838511, mismatch
    Results written to file: ip_8.8.8.8.txt
```

* Username search
```bash
$ python data_digger.py -un "username"

    Github: no
    Instagram: no
    X: no
    TikTok: yes
    SoundCloud: yes
    Results written to file: un_username.txt
```

* Multi-input search
```bash
$ python data_digger.py -n "Dwight Schrute" -ip "8.8.8.8"

    First name: Dwight (src: 3)
    Last name: Schrute (src: 3)
    Address: Rural Rt. 6, Honesdale, PA 18431 (src: 1)
    Phone number: 7175550177 (src: 1)
    Description: fictional character in NBC's The Office (src: 1)
    Results written to file: n_dwight_schrute.txt


    IP: 8.8.8.8
    ISP: AS15169 Google LLC
    Location: source1: 37.4056,-122.0775 / source2: 39.03,-77.5 / source3: 37.3860517,-122.0838511, mismatch
    Results written to fie: ip_8.8.8.8.txt
```

