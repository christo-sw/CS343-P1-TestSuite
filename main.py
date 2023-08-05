import json.decoder
import random
import requests


def get_port() -> str:
    while True:
        port = input("Port number: ")
        try:
            int(port)
        except ValueError:
            print("Please enter a valid port number")
        else:
            return port


def get_token() -> str:
    return input("GitHub API Token (basic), or just press enter to leave blank: ")


def get_num_tests() -> int:
    while True:
        num_tests = input("Number of tests (min 1, max 100): ")
        try:
            num_tests = int(num_tests)
        except ValueError:
            print("Please enter a valid number of tests")
        else:
            if num_tests <= 0:
                num_tests = 1
            elif num_tests > 100:
                num_tests = 100

            return num_tests


def get_config_file(filename):
    config_file = None

    try:
        config_file = open(filename, "r+")
    except IOError:
        open(filename, "x")
        return get_config_file(filename)
    else:
        return config_file


def get_values_from_file(config_file) -> (str, str, int):
    port = ""
    token = ""
    num_tests = -1

    lines = config_file.readlines()

    if len(lines) != 0:
        for line in lines:
            key_and_val = line.split("=")
            match key_and_val[0].lower():
                case "port":
                    if len(key_and_val) > 1:
                        port = key_and_val[1].strip()
                        try:
                            int(port)
                        except ValueError:
                            port = None

                case "token":
                    if len(key_and_val) > 1:
                        token = key_and_val[1].strip()

                case "num_tests":
                    if len(key_and_val) > 1:
                        num_tests = key_and_val[1].strip()
                        try:
                            num_tests = int(num_tests)
                        except ValueError:
                            num_tests = None
                        else:
                            if num_tests <= 0:
                                num_tests = 1
                            elif num_tests > 100:
                                num_tests = 100

    return port, token, num_tests


def get_missing_values_from_user_and_update_file(config_file, port, token, num_tests) -> (str, str, int):

    if port is None:
        port = get_port()
        config_file.write(f"PORT={port}\n")

    if token is None:
        token = get_token()
        config_file.write(f"TOKEN={token}\n")

    if num_tests is None:
        num_tests = get_num_tests()
        config_file.write(f"NUM_TESTS={num_tests}")

    return port, token, num_tests


def test():
    config_file = get_config_file("config.txt")
    (port, token, num_tests) = get_values_from_file(config_file)
    (port, token, num_tests) = get_missing_values_from_user_and_update_file(config_file, port, token, num_tests)
    config_file.close()

    random_num = random.randint(0, 100000000)
    endpoint = "https://api.github.com/users?since=" + str(random_num) + "&per_page=" + str(num_tests)

    headers = {}
    if token != "":
        headers = {"Authorization": "Bearer " + token}

    users = None
    try:
        users = requests.get(endpoint, headers=headers)
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not get response from GitHub. Is your internet working? Cannot run test suite.")
        exit()

    i = 0
    skip_count = 0
    pass_count = 0
    fail_count = 0
    test_count = 0

    for user in users.json():
        i = i + 1
        print(f"============ TEST {i} - {user['login']} [{user['type']}] ============")

        test_count = test_count + 1

        username = user["login"]

        local_response = None
        try:
            local_response = requests.get("http://localhost:" + port + "/users/" + username)
        except requests.exceptions.ConnectionError:
            print("ERROR: Could not get response from local server. Is your server running? Skipping test.")
            skip_count = skip_count + 1
            continue

        ground_truth_response = None
        try:
            ground_truth_response = requests.get("https://api.github.com/users/" + username, headers=headers)
        except requests.exceptions.ConnectionError:
            print("ERROR: Could not get response from GitHub. Is your internet working? Skipping test.")
            skip_count = skip_count + 1
            continue

        local_data = None
        try:
            local_data = local_response.json()
        except json.decoder.JSONDecodeError:
            print("ERROR: Could not parse local response into JSON. Ensure your response is not malformed and that"
                  " your server has not crashed. Skipping test.")
            skip_count = skip_count + 1
            continue

        ground_truth_data = None
        try:
            ground_truth_data = ground_truth_response.json()
        except json.decoder.JSONDecodeError:
            print("ERROR: Could not parse the GitHub API response into JSON. This is a highly unexpected error."
                  "Debug manually. Skipping test.")
            skip_count = skip_count + 1
            continue

        if local_response.status_code == ground_truth_response.status_code:
            pass_count = pass_count + 1
            print(f"\tPASSED\tStatus Code")
        else:
            fail_count = fail_count + 1
            print(f"\tFAILED\tStatus Code -> Expected {ground_truth_response.status_code},"
                  f"found {local_response.status_code}")

        for val in local_data:
            if local_data[val] == ground_truth_data[val]:
                pass_count = pass_count + 1
                print(f"\tPASSED\t{val}")
            else:
                fail_count = fail_count + 1
                print(f"\tFAILED\t{val} -> Expected {ground_truth_data[val]}, found {local_data[val]} ")

    print("")
    print(f"============ TEST RESULTS ============")
    print(f"PASSED: \t\t\t{pass_count}\nFAILED: \t\t\t{fail_count}\nSKIPPED: \t\t\t{skip_count}")


if __name__ == '__main__':
    test()
