# Standard library
import re
from typing import Optional
# Third party
import zeep
import zeep.exceptions
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_not_exception_type
import requests


class LookupVat:
    def __init__(self) -> None:
        self.settings = zeep.Settings(
            strict=False,
            xml_huge_tree=True,
        )
        self.wdsl = 'http://ec.europa.eu/taxation_customs/vies/checkVatService.wsdl'
        self.client: Optional[zeep.Client] = None
        self.address_regex_dict: dict = {}
        self.load_address_dict()

    def load_address_dict(self):
        """
        This function has individual country address regexes for addresses retrieved from VIES.
        Each country address is unique. Some countries, e.g. DE and ES, do not return company name
        and address details, those are listed as 'None'.
        We only use company name, street address, postal code and city. Some countries, e.g. PT, return
        further address details like the municipality, these are parsed but not included in the returned
        VAT lookup result dict.
        :return:
        """
        self.address_regex_dict = {
            'AT': r'^(?P<street>.*)\n(?P<postal_code>\S+)\s+(?P<city>.*)$',
            'BE': r'^(?P<street>.*)\n(?P<postal_code>\S+)\s+(?P<city>.*)$',
            'BG': r'^(?P<street>.*),\s(?P<city>.*)\s(?P<postal_code>\d+)$',
            'CY': r'^(?P<street>.*)\n(?P<postal_code>\S+)\s+(?P<city>.*)$',
            'CZ': r'',
            'DE': None,
            'DK': r'^(?P<street>.*)\n(?P<postal_code>\S+)\s+(?P<city>.*)\n$',
            'EE': r'^(?P<street>.*)\s{3}(?P<postal_code>\d+)\s+(?P<city>.*)$',
            'EL': r'^(?P<street>\S+\s\w+)\s{3,}(?P<postal_code>\S+\S+)\s-\s(?P<city>.*)$',
            'ES': None,
            'FI': r'^(?P<street>.*)\n(?P<postal_code>\S+)\s+(?P<city>.*)$',
            'FR': r'^(?P<street>.*)\n(?P<postal_code>\d+)\s+(?P<city>.*)$',
            'HR': r'^(?P<street>.*),\s+(?P<city>.*),\s+(?P<postal_code>.*)$',
            'HU': r'^(?P<street>.*)\s+(?P<postal_code>\d+)\s+(?P<city>.*)$',
            'IE': r'',
            'IT': r'^(?P<street>.*)\n(?P<postal_code>\d+)\s+(?P<city>.*)\s\S{2}\n$',
            'LT': r'^(?P<street>.*),\s+(?P<city>.*),\s+((?P<postal_code>LT\d{5})|(?P<province>.*))$',
            'LU': r'^(?P<street>.*)\n(?P<postal_code>\S+)\s+(?P<city>.*)$',
            'LV': r'^(?P<street>.*),\s+(?P<city>.*),\s+(?P<postal_code>\S+)$',
            'MT': r'',
            'NL': r'^\n(?P<street>.*)\n(?P<postal_code>\S+)\s+(?P<city>.*)\n$',
            'NO': r'',
            'PL': r'',
            'PT': r'^(?P<street>.*)\n(?P<municipality>\S+)\n(?P<postal_code>\S+)\s+(?P<city>.*)$',
            'RO': None,
            'RS': r'',
            'SE': r'^(?P<street>.*)\n(?P<postal_code>\S+\s\S+)\s+(?P<city>.*)$',
            'SI': r'^(?P<street>.*),\s+(?P<postal_code>\d{4})\s+(?P<city>.*)$',
            'SK': r'^(?P<street>.*)\n(?P<postal_code>\S+)\s(?P<city>.*)\n(?P<country>.*)$',
            'XI': r'',
        }

    # Tenacity decorator, number of attempts = 10, time increasing exponentially
    @retry(
        reraise=True,
        retry=retry_if_not_exception_type(requests.HTTPError),
        stop=stop_after_attempt(10),
        wait=wait_exponential(multiplier=1, max=20)
    )
    def connect(self):
        print("Connecting to VIES web service...")
        # Creating client object will try connecting. Note Request exceptions are used.
        # As this is a SOAP session the connection will verify the network service is available
        # and then also initialise the Zeep client.
        try:
            self.client = zeep.Client(self.wdsl, settings=self.settings)
        # If the URL is invalid no point in retrying
        except requests.HTTPError as e:
            print(f"Invalid URL, exception = {e.response.reason}: {e.response.status_code}")
            raise requests.HTTPError(f"{e}")
        except requests.ConnectionError as e:
            print(f"Requests connection exception, retry will be attempted.\n"
                  f"Exception = {e}")
            raise requests.ConnectionError(f"{e}")
        # This will catch both connect and read timeout exceptions
        except requests.Timeout as e:
            print(f"Requests timeout exception, retry will be attempted.\n"
                  f"Exception = {e}")
            raise requests.Timeout
        except requests.RequestException as e:
            print(f"There was a general Requests, or supporting library, exception. Retry will be attempted.\n"
                  f"Exception = {e}")
            raise requests.RequestException(f"{e}")
        except Exception as e:
            print(f"There was a general exception which may also be a Zeep error, retry will be attempted.\n"
                  f"Exception = {e}")
            raise Exception(f"{e}")
        print(f"...connection successful.\n")

    # Number of attempts = 5
    @retry(
        reraise=True,
        retry=retry_if_not_exception_type(UnboundLocalError),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, max=20)
    )
    def lookup_vat(self, vat_no: str, result: dict) -> dict:
        """
        Lookup a VAT number. This can be called once only by 'check_vat.py' for a single VAT number or
        called repeatedly (in one connection) for a batch of lookups.
        :param result: 
        :param vat_no:
        :return result:
        """

        # Split VAT to country code and number for lookup in VIES
        country_code = vat_no[:2]
        vat_number = vat_no[2:]

        # Note there is 'response' which is the web services server response (as like Requests) and
        # there is result. Result has customised values set.
        try:
            if self.client is not None:
                response = self.client.service.checkVat(countryCode=country_code, vatNumber=vat_number)
            else:
                raise UnboundLocalError
        # This shouldn't ever occur if the Zeep client object had been properly initialised.
        # This will not do a Tenacity retry, see @retry decorator above, it will return to check_vat.py
        # which will terminate the program.
        except UnboundLocalError:
            raise UnboundLocalError(f"Program error, self.client attribute has not been assigned before use")
        # There are many potential causes for error here particularly as VIES passes on queries to member states,
        # and they may, in turn, return errors. All of these will be allowed to retry with Tenacity.
        except zeep.exceptions.Fault as e:
            # Go through list of possible failures. Note have to match against 'e.message', not just 'e'.
            # Possible result['ret_code'] values are:
            # 0 - Network lookup success, this does not necessarily mean the VAT number is valid though
            # 1 - A hard failure, processing cannot continue
            # 2 - A specific vat lookup failed, note the failure and go to next lookup
            if e.message == 'GLOBAL_MAX_CONCURRENT_REQ':
                result['ret_code'] = 1
                result['err_msg'] = f"The VIES system is currently overloaded, please try again later."
            elif e.message == 'GLOBAL_MAX_CONCURRENT_REQ_TIME':
                result['ret_code'] = 1
                result['err_msg'] = f"The VIES system has too many requests resulting in delays in response, " \
                                    f"please try again later."
            elif e.message == 'MS_MAX_CONCURRENT_REQ':
                result['ret_code'] = 1
                result['err_msg'] = f"The member state '{country_code}' that the VIES system is " \
                                    f"trying to contact is currently overloaded, try again later."
            elif e.message == 'MS_MAX_CONCURRENT_REQ_TIME':
                result['ret_code'] = 1
                result['err_msg'] = f"The member state '{country_code}' that the VIES system is " \
                                    f"trying to contact has too many requests resulting in delays in " \
                                    f"response, try again later."
            elif e.message == 'TIMEOUT':
                result['ret_code'] = 1
                result['err_msg'] = f"There was a timeout trying to reach the VIES system, try again later."
            elif e.message == 'SERVICE_UNAVAILABLE':
                result['ret_code'] = 1
                result['err_msg'] = f"The VIES system is currently unavailable and may be undergoing " \
                                    f"maintenance, try again later."
            elif e.message == 'SERVER_BUSY':
                result['ret_code'] = 1
                result['err_msg'] = f"The VIES system is too busy to service your request, try again later."
            elif e.message == 'MS_UNAVAILABLE':
                result['ret_code'] = 1
                result['err_msg'] = f"The VIES system was is currently unable to contact the requested " \
                                    f"member state database, try another member state " \
                                    f"or try this lookup later."
            elif e.message == 'IP_BLOCKED':
                result['ret_code'] = 1
                result['err_msg'] = f"WARNING - the querying server IP address has been blocked by VIES, " \
                                    f"please inform IT support immediately."
            elif e.message == 'VAT_BLOCKED':
                result['ret_code'] = 2
                result['err_msg'] = f"The VAT number being queried, '{vat_no}', is BLOCKED. This may be " \
                                    f"an indication of financial issues. PLEASE INFORM YOUR FINANCE " \
                                    f"DEPARTMENT IMMEDIATELY."
            elif e.message == 'INVALID_INPUT':
                result['ret_code'] = 2
                result['err_msg'] = f"The VAT number, '{vat_no}', you are looking up is invalid, please " \
                                    f"check it and retry."
            # Catchall in case of other error
            else:
                result['ret_code'] = 1
                result['err_msg'] = f"There was an error, '{e}' trying to look up the VAT number " \
                                    f"{vat_no} in the VIES system."
            # Tenacity will retry the lookup, see Tenacity parameters above, if the retries defined in
            # 'stop_after_attempt' are exceeded then the exception will be passed back to the calling
            # function which will usually be 'do_lookup' in 'check_vat.py'.
            raise RuntimeError(result)

        # There is a response from VIES and the VAT number is valid
        if response['valid']:
            result['valid'] = True
            result['vat_enabled'] = True
            result['country_code'] = response['countryCode']
            # # CHECK RAW RESPONSE
            # print("\nRaw response...")
            # print(response)
            # # CHECK RAW RESPONSE
            # Get address regex and parse address line if available
            address_regex = self.address_regex_dict[country_code]
            if address_regex is not None:
                result['company_name'] = response['name']
                try:
                    match = re.match(rf"{address_regex}", response['address'])
                except Exception as e:
                    print(f"There was an error = {e}.")
                    return result
                if match:
                    try:
                        if match.group('street'):
                            result['street'] = match.group('street').strip()
                        if match.group('postal_code'):
                            result['postal_code'] = match.group('postal_code').strip()
                        if match.group('city'):
                            result['city'] = match.group('city').strip()
                    except IndexError as e:
                        print(f"There was an error, '{e}', parsing the address.\n"
                              f"Is the address regex for country {country_code} defined?")
                        return result
                    else:
                        result['has_details'] = True
                        print(f"\nCompany Name: {result['company_name']}")
                        print(f"Address:")
                        print(f"\t{result['street']}")
                        print(f"\t{result['postal_code']} {result['city']}")
                        print(f"\t{result['country_code']}\n")
            else:
                print(f"The member state {result['country_code']} does not supply company name or address details.")
            # Only change ret_code from -1 to 0 if all processing is OK.
            result['ret_code'] = 0
            return result
        else:
            # There is a response but the key 'valid' is not true, that is there is a lookup failure,
            # the VAT number does not exist in VIES.
            # The variable, result['valid'], is not changed from False
            print(f"The VAT number, {vat_no}, does not exist in the VIES database, it is NOT valid.")
            result['err_msg'] = f"The VAT number, {vat_no}, does not exist in the VIES database, " \
                                f"it is NOT valid."
            return result


def main():
    lookup = LookupVat()
    try:
        lookup.connect()
    except Exception as e:
        print(f"We tried to connect and it didn't work, the error was:\n{e}")
        quit()
    print(f"Connection is OK and valid client object.\n")


if __name__ == '__main__':
    main()
