import json.decoder
import random
import requests

from termcolor import colored, cprint


def print_success(msg):
    success_banner = colored("PASSED", "white", "on_green")
    print(f"\t{success_banner}\t" + msg)


def print_failure(msg):
    failure_banner = colored("FAILED", "white", "on_red")
    print(f"\t{failure_banner}\t" + msg)


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
    token = input("GitHub API Token (basic), or just press enter to leave blank: ")

    if token.strip() != "":
        return token.strip()
    else:
        return "_"


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


def get_test_type() -> int:
    while True:
        test_type = input("Test type (0 - Users, 1 - Repos, 2 - Both): ")
        try:
            test_type = int(test_type)
        except ValueError:
            print("Please enter a valid number of tests")
        else:
            if test_type < 0 or test_type > 2:
                print("Please enter a valid test type")
            else:
                return test_type


def get_config_file(filename):
    config_file = None

    try:
        config_file = open(filename, "r+")
        return config_file
    except IOError:
        config_file = open(filename, "x")
        config_file.close()
        config_file = get_config_file(filename)
        return config_file


def get_values_from_file(config_file) -> (str, str, int, list, int):
    port = None
    token = None
    num_tests = None
    users = None
    test_type = None

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

                case "users":
                    if len(key_and_val) > 1:
                        users = key_and_val[1].strip()
                        try:
                            users = json.loads(users)
                        except json.decoder.JSONDecodeError:
                            users = None

                case "test_type":
                    if len(key_and_val) > 1:
                        test_type = key_and_val[1].strip()
                        try:
                            test_type = int(test_type)
                        except ValueError:
                            test_type = None
                        else:
                            if test_type < 0 or test_type > 2:
                                print("ERROR: Invalid type of test selected. Please choose either 0, 1, or 2")
                                print("[0 - Users, 1 - Repos, 2 - Both")
                                exit()

    return port, token, num_tests, users, test_type


def get_missing_values_from_user_and_update_file(config_file, port, token, num_tests, test_type) \
        -> (str, str, int, int):
    if port is None:
        port = get_port()
        config_file.write(f"PORT={port}\n")

    if token is None:
        token = get_token()
        config_file.write(f"TOKEN={token}\n")

    if num_tests is None:
        num_tests = get_num_tests()
        config_file.write(f"NUM_TESTS={num_tests}\n")

    if test_type is None:
        test_type = get_test_type()
        config_file.write(f"TEST_TYPE={test_type}\n")

    return port, token, num_tests, test_type


def get_test_parameters_from_config_file() -> (str, str, int, list, int):
    config_file = get_config_file("config.txt")
    (port, token, num_tests, users, test_type) = get_values_from_file(config_file)
    (port, token, num_tests, test_type) = \
        get_missing_values_from_user_and_update_file(config_file, port, token, num_tests, test_type)
    config_file.close()
    return port, token, num_tests, users, test_type


def get_random_users(num_tests, headers):
    random_num = random.randint(0, 100000000)
    endpoint = "https://api.github.com/users?since=" + str(random_num) + "&per_page=" + str(num_tests)

    users = None
    try:
        users = requests.get(endpoint, headers=headers)
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not get response from GitHub. Is your internet working? Cannot run the test suite.")
        exit()

    # Check for rate limit
    if users.status_code == 429:
        print("The test suite hit the GitHub API rate limit. "
              "Please wait a while, or add an API token if you have not yet done so. Cannot run the test suite.")
        exit()

    user_list = []
    for user in users.json():
        user_list.append(user["login"])

    return user_list


def test_user(username, headers, port, skip_count, pass_count, fail_count) -> (int, int, int):
    # Get local and ground truth responses
    local_response = None
    try:
        local_response = requests.get("http://localhost:" + port + "/users/" + username)
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not get response from local server. Is your server running? Skipping test.")
        skip_count = skip_count + 1
        return skip_count, pass_count, fail_count

    ground_truth_response = None
    try:
        ground_truth_response = requests.get("https://api.github.com/users/" + username, headers=headers)
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not get response from GitHub. Is your internet working? Skipping test.")
        skip_count = skip_count + 1
        return skip_count, pass_count, fail_count

    # Check for rate limit
    if ground_truth_response.status_code == 429:
        print("The test suite hit the GitHub API rate limit. "
              "Please wait a while, or add an API token if you have not yet done so. Skipping test.")
        skip_count = skip_count + 1
        return skip_count, pass_count, fail_count

    # Parse local and ground truth data from responses
    local_data = None
    try:
        local_data = local_response.json()
    except json.decoder.JSONDecodeError:
        print("ERROR: Could not parse local response into JSON. Ensure your response is not malformed and that"
              " your server has not crashed. Skipping test.")
        skip_count = skip_count + 1
        return skip_count, pass_count, fail_count

    ground_truth_data = None
    try:
        ground_truth_data = ground_truth_response.json()
    except json.decoder.JSONDecodeError:
        print("ERROR: Could not parse the GitHub API response into JSON. This is a highly unexpected error."
              "Debug manually. Skipping test.")
        skip_count = skip_count + 1
        return skip_count, pass_count, fail_count

    if local_response.status_code == ground_truth_response.status_code:
        pass_count = pass_count + 1
        print_success(f"Status Code")
    else:
        fail_count = fail_count + 1
        print_failure(f"Status Code -> Expected {ground_truth_response.status_code}, "
                      f"found {local_response.status_code}")

    for val in local_data:
        if ground_truth_data[val] is None or ground_truth_data[val] == "":
            if local_data[val] is None or local_data[val] == "":
                pass_count = pass_count + 1
                print_success(f"{val}")
            else:
                fail_count = fail_count + 1
                print_failure(f"{val} -> Expected {ground_truth_data[val]}, found {local_data[val]} ")
        elif local_data[val] == ground_truth_data[val]:
            pass_count = pass_count + 1
            print_success(f"{val}")
        else:
            fail_count = fail_count + 1
            print_failure(f"{val} -> Expected {ground_truth_data[val]}, found {local_data[val]} ")

    return skip_count, pass_count, fail_count


def test_user_repos(username, headers, port, skip_count, pass_count, fail_count) -> (int, int, int):
    # Get local and ground truth responses
    local_response = None
    try:
        local_response = requests.get("http://localhost:" + port + "/users/" + username + "/repos")
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not get response from local server. Is your server running? Skipping test.")
        skip_count = skip_count + 1
        return skip_count, pass_count, fail_count

    ground_truth_response = None
    try:
        ground_truth_response = requests.get("https://api.github.com/users/" + username + "/repos", headers=headers)
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not get response from GitHub. Is your internet working? Skipping test.")
        skip_count = skip_count + 1
        return skip_count, pass_count, fail_count

    # Check for rate limit
    if ground_truth_response.status_code == 429:
        print("The test suite hit the GitHub API rate limit. "
              "Please wait a while, or add an API token if you have not yet done so. Skipping test.")
        skip_count = skip_count + 1
        return skip_count, pass_count, fail_count

    # Parse local and ground truth data from responses
    local_data = None
    try:
        local_data = local_response.json()
    except json.decoder.JSONDecodeError:
        print("ERROR: Could not parse local response into JSON. Ensure your response is not malformed and that"
              " your server has not crashed. Skipping test.")
        skip_count = skip_count + 1
        return skip_count, pass_count, fail_count

    ground_truth_data = None
    try:
        ground_truth_data = ground_truth_response.json()
    except json.decoder.JSONDecodeError:
        print("ERROR: Could not parse the GitHub API response into JSON. This is a highly unexpected error."
              "Debug manually. Skipping test.")
        skip_count = skip_count + 1
        return skip_count, pass_count, fail_count

    # Test for response code match
    if local_response.status_code == ground_truth_response.status_code:
        pass_count = pass_count + 1
        print_success(f"Status Code")
    else:
        fail_count = fail_count + 1
        print_failure(f"Status Code -> Expected {ground_truth_response.status_code}, "
                      f"found {local_response.status_code}")

    local_data_len = None
    try:
        local_data_len = len(local_data)
    except AttributeError:
        local_data_len = 0  # 404 Message

    ground_truth_data_len = None
    try:
        ground_truth_data_len = len(ground_truth_data)
    except AttributeError:
        ground_truth_data_len = 0  # 404 Message

    # Test for repo count match
    if local_data_len == ground_truth_data_len:
        pass_count = pass_count + 1
        print_success(f"Repo Count")
    else:
        fail_count = fail_count + 1
        print_failure(f"Repo Count -> Expected {ground_truth_data_len}, "
                      f"found {local_data_len}")

    for i in range(0, ground_truth_data_len):
        local_repo = local_data[i]
        ground_truth_repo = ground_truth_data[i]

        print(f"\n=> REPO {ground_truth_repo['name']}")

        for val in local_repo:
            if ground_truth_repo[val] is None or ground_truth_repo[val] == "":
                if local_repo[val] is None or local_repo[val] == "":
                    pass_count = pass_count + 1
                    print_success(f"{val}")
                else:
                    fail_count = fail_count + 1
                    print_failure(f"{val} -> Expected {ground_truth_repo[val]}, found {local_repo[val]} ")
            elif local_repo[val] == ground_truth_repo[val]:
                pass_count = pass_count + 1
                print_success(f"{val}")
            else:
                fail_count = fail_count + 1
                print_failure(f"{val} -> Expected {ground_truth_repo[val]}, found {local_repo[val]}")

    return skip_count, pass_count, fail_count


def test_users(port, token, num_tests, users):
    # Use GitHub auth token if available
    headers = {}
    if token != "_":
        headers = {"Authorization": "Bearer " + token}

    if users is None:
        users = get_random_users(num_tests, headers)

    # Testing metrics
    i = 0
    skip_count = 0
    pass_count = 0
    fail_count = 0
    test_count = 0

    # Run through all the random users and test each one-by-one
    for username in users:
        i = i + 1
        test_count = test_count + 1
        print(f"\n============ TEST {i} - {username} ============")

        (skip_count, pass_count, fail_count) = \
            test_user(username, headers, port, skip_count, pass_count, fail_count)

    # Print test results
    print(f"\n============ TEST RESULTS ============")
    print(f"PASSED: \t\t\t{pass_count}\nFAILED: \t\t\t{fail_count}\nSKIPPED: \t\t\t{skip_count}")


def test_repos(port, token, num_tests, users):
    # Use GitHub auth token if available
    headers = {}
    if token != "_":
        headers = {"Authorization": "Bearer " + token}

    if users is None:
        users = get_random_users(num_tests, headers)

    # Testing metrics
    i = 0
    skip_count = 0
    pass_count = 0
    fail_count = 0
    test_count = 0

    # Run through all the random users and test each one's repos
    for username in users:
        i = i + 1
        test_count = test_count + 1
        print(f"\n============ TEST {i} - {username} ============")

        (skip_count, pass_count, fail_count) = \
            test_user_repos(username, headers, port, skip_count, pass_count, fail_count)

    # Print test results
    print(f"\n============ TEST RESULTS ============")
    print(f"PASSED: \t\t\t{pass_count}\nFAILED: \t\t\t{fail_count}\nSKIPPED: \t\t\t{skip_count}")


def decide_test_mode():
    (port, token, num_tests, users, test_type) = get_test_parameters_from_config_file()

    # Test type should always be one of these three values
    match test_type:
        case 0:
            test_users(port, token, num_tests, users)

        case 1:
            test_repos(port, token, num_tests, users)

        case 2:
            test_users(port, token, num_tests, users)
            test_repos(port, token, num_tests, users)


if __name__ == '__main__':
    decide_test_mode()
