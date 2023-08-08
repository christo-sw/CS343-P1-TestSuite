# CS344 Project 1 Test Suite

This test suite is intended for preliminary testing, as we will apparently be getting an official test suite at a later time.

# Installation

First, clone the repository to any place on your system

```bash
git clone https://github.com/christo-sw/CS343-P1-TestSuite.git
```

Navigate into the cloned repository

```bash
cd CS343-P1-TestSuite
```

>**NOTE:** If you do not already have virtualenv installed on your system, do this next:
>
>```bash
>python3 -m pip install --user virtualenv
>```

Next, create a virtual environment in the current directory

```bash
python3 -m venv env
```

Activate the virtual environment

```bash
source env/bin/activate
```

Install the test suite requirements

```bash
python3 -m pip install -r requirements.txt
```

# Usage

After installation is done, you can run the test suite with

```bash
python3 test.py
```

The test suite will ask you to enter the required information and settings, and store them in a file called `config.txt`
This file will be read at the start of every test run, so you will only have to enter your settings once.

Changes can and should be made directly to the config file. Any missing fields will be requested when you run the test
suite again, and will be promptly written to the config file.

There are currently 5 fields to specify
- `PORT` - ***[required]*** any number
- `TOKEN` - your classic (not fine-grained) GitHub access token, can be left blank (saved as "_")
- `NUM_TESTS` - ***[required]*** 1-100 (I recommend 8 due to rate limits)
- `TEST_TYPE` - ***[required]*** 0 - Users, 1 - Repos, 2 - Both
- `USERS` - an optional array of usernames, will override `NUM_TESTS`

An example `config.txt` could look like:

```text
PORT=8080
TOKEN=ghp_asdfAQ$4qhfancytoken423Gwerhr
NUM_TESTS=8
TEST_TYPE=1
USERS=["christo-sw", "Jacques2Marais"]
```

>**NOTE:** The `USERS` array be must manually be added to the `config.txt` file, the test suite will not prompt you for it.
> Also, you are free to leave the GitHub access token blank, though this will limit the number of tests you can run.
> To add a token, simply edit the config file.

# Contributions

If anyone feels passionately about adding something to or changing something about this test suite, you are free to do so.
I'm not exactly sure how to set it up, but shoot me a WhatsApp and we can even do pull requests and whatnot. 
Furthermore, please do not hesitate to inform me of any bugs. Thanks! :D