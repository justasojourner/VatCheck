import json
# Third party
import requests
# Application
from vat_utils import get_country_name_from_code


def check_service_status() -> list:
    """
    Check status of the EU member state VAT checking services in VIES
    Service URL: https://ec.europa.eu/taxation_customs/vies/rest-api/check-status
    :return: List of unavailable member states. Calling function will do simple check
    of returned list to see if member state being VAT checked is not available.
    """
    unavailable_countries: list = []
    host = 'ec.europa.eu'
    service = '/taxation_customs/vies/rest-api/check-status'
    headers = {
        "user-agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0",
        'Content-type': 'application/json',
    }
    url: str = 'https://' + host + service

    try:
        res = requests.get(url, headers=headers)
    # Note: Status code cannot be set as if any exceptions are raised the res object,
    # and therefore the res.status_code, cannot be known.
    # Note: Requests.HTTPError does NOT catch returned 404, and other HTTP failure results,
    # they are not considered as application level (exception) errors
    except requests.HTTPError as e:
        print(f"Invalid URL, exception = {e.response.reason}: {e.response.status_code}")
        raise requests.HTTPError(f"{e}")
    except requests.ConnectionError as e:
        print(f"Requests connection exception, retry will be attempted.\n"
              f"Exception = {e}")
        raise requests.ConnectionError(f"{e}")
    except requests.Timeout as e:
        print(f"Requests timeout exception, retry will be attempted.\n"
              f"Exception = {e}")
        raise requests.Timeout(f"{e}")
    except requests.RequestException as e:
        print(f"There was a general Requests, or supporting library, exception.\n"
              f"Exception = {e}")
        raise requests.RequestException(f"{e}")
    except Exception as e:
        print(f"There was a general exception querying the VIES member state status checker.\n"
              f"Exception = {e}")
        raise RuntimeError(f"{e}")

    # Got a connection, now check response status code
    status_code = res.status_code
    if status_code == 200:
        # # Show raw response
        # print()
        # print(json.dumps(res.json(), indent=4))
        # print()
        # # Show raw response
        result = json.loads(res.content)
        if "vow" in result:
            if result['vow']['available'] is True:
                print("The VIES member state status service is available\n")
                countries = result['countries']
                for country in countries:
                    if country['availability'] == 'Unavailable':
                        unavailable_countries.append(country['countryCode'])
            else:
                print("The VIEW member state status service website is up "
                      "but the status checker is not available\n")
    elif 400 <= status_code <= 499:
        print(f"Status code: {status_code}")
        print(f"URL invalid")
        raise ConnectionError(f"VIES status checker error code: {status_code}")
    elif 500 <= status_code <= 599:
        print(f"Status code: {status_code}")
        print(f"Server error")
        raise ConnectionError(f"VIES status checker error code: {status_code}")
    else:
        # Otherwise some other error causing failure, ret_code changed to 1
        print(f"Status code: {status_code}")
        print(f"The check failed")
        raise ConnectionError(f"VIES status checker error code: {status_code}")
    return unavailable_countries


def main():
    try:
        countries = check_service_status()
    except Exception as e:
        print(f"There was an error, '{e}', while checking the member states status.")
        exit()
    if countries:
        # Only run code to get list of country names if there are unavailable countries
        country_codes: dict = get_country_name_from_code()
        for country in countries:
            print(f"The VAT lookup service for member state {country}, "
                  f"{country_codes[country]}, is not available")
    else:
        print(f"All member state VAT services are available.")


if __name__ == '__main__':
    main()
