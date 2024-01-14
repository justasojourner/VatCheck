# Standard library
import re
# Application
# import soap_check_eu_vat
import check_ch_vat
import check_uk_vat
import check_no_vat
import new_check_eu_vat


class CheckVat:
    """
    Note: the code for EU lookups to VIES now uses Tenacity to do retry attempts in case of network errors.
    Because of the setup of Tenacity we MUST use exception checking for the result otherwise the final
    exception will not be handled.
    """
    def __init__(self) -> None:
        self.vat_no: str = ''
        self.country_code: str = ''
        self.country_type: str = ''
        self.countries: dict = {}
        self.result: dict = {}
        # Instantiate all the VAT service lookup classes, a connection check will be run on the SOAP services
        try:
            # self.lookup_eu_vat = check_eu_vat.LookupVat()
            self.lookup_eu_vat = new_check_eu_vat.LookupVat()
            self.lookup_ch_vat = check_ch_vat.LookupVat()
            self.lookup_no_vat = check_no_vat.LookupVat()
            self.lookup_uk_vat = check_uk_vat.LookupVat()
        except Exception as e:
            print(f"There was an exception, {e}, connecting to a VAT lookup web service")
            raise RuntimeError(f"There was an exception, {e}, connecting to a VAT lookup web service")
        self.load_countries_dict()

    def load_countries_dict(self) -> None:
        self.countries = {
            'AT': {'name': 'Austria', 'eu': True, 'rx': r'ATU\d{8}'},
            'BE': {'name': 'Belgium', 'eu': True, 'rx': r'BE(0|1)\d{9}'},
            'BG': {'name': 'Bulgaria', 'eu': True, 'rx': r'BG\d{9,10}'},
            'CH': {'name': 'Switzerland', 'eu': False, 'rx': r'CHE\d{9}'},
            'CY': {'name': 'Cyprus', 'eu': True, 'rx': r'CY\d{8}[A-Z]'},
            'CZ': {'name': 'Czech Republic', 'eu': True, 'rx': r'CZ\d{8,10}'},
            'DE': {'name': 'Germany', 'eu': True, 'rx': r'DE\d{9}'},
            'DK': {'name': 'Denmark', 'eu': True, 'rx': r'DK\d{8}'},
            'EE': {'name': 'Estonia', 'eu': True, 'rx': r'EE\d{9}'},
            'EL': {'name': 'Greece', 'eu': True, 'rx': r'EL\d{9}'},
            'ES': {'name': 'Spain', 'eu': True, 'rx': r'ES.{9}'},
            'FI': {'name': 'Finland', 'eu': True, 'rx': r'FI\d{8}'},
            'FR': {'name': 'France', 'eu': True, 'rx': r'FR.{11}'},
            'GB': {'name': 'United Kingdom', 'eu': False, 'rx': r'GB\d{9}'},
            'HR': {'name': 'Croatia', 'eu': True, 'rx': r'HR\d{11}'},
            'HU': {'name': 'Hungary', 'eu': True, 'rx': r'HU\d{8}'},
            'IE': {'name': 'Ireland', 'eu': True, 'rx': r'IE\d{7}[A-Z]|\d[A-Z]\d{5}[A-Z]'},
            'IT': {'name': 'Italy', 'eu': True, 'rx': r'IT\d{11}'},
            'LI': {'name': 'Liechtenstein', 'eu': False, 'rx': r''},
            'LT': {'name': 'Lithuania', 'eu': True, 'rx': r'LT\d{9}(\d{3})?'},
            'LU': {'name': 'Luxembourg', 'eu': True, 'rx': r'LU\d{8}'},
            'LV': {'name': 'Latvia', 'eu': True, 'rx': r'LV\d{11}'},
            'MT': {'name': 'Malta', 'eu': True, 'rx': r'MT\d{8}'},
            'NL': {'name': 'Netherlands', 'eu': True, 'rx': r'NL\d{9}B\d{2}'},
            'NO': {'name': 'Norway', 'eu': False, 'rx': r'NO\d{9}'},
            'PL': {'name': 'Poland', 'eu': True, 'rx': r'PL\d{10}'},
            'PT': {'name': 'Portugal', 'eu': True, 'rx': r'PT\d{9}'},
            'RO': {'name': 'Romania', 'eu': True, 'rx': r'RO\d{2,10}'},
            'RS': {'name': 'Serbia', 'eu': False, 'rx': None},
            'SE': {'name': 'Sweden', 'eu': True, 'rx': r'SE\d{12}'},
            'SI': {'name': 'Slovenia', 'eu': True, 'rx': r'SI\d{8}'},
            'SK': {'name': 'Slovakia', 'eu': True, 'rx': r'SK\d{10}'},
            'SM': {'name': 'San Marino', 'eu': False, 'rx': r'SM\d{5}'},
            'XI': {'name': 'Northern Ireland - United Kingdom', 'eu': True, 'rx': r'XI\d{9}'},
        }

    def do_lookup(self, vat_no: str) -> dict:
        """
        Do the VAT lookup. VAT is checked for the country code and appropriate service called.
        The key 'ret_code' is a return code to indicate success or fail of the function, it is
        set to -1 on initialisation, if VAT lookup is successful it is changed to 0. If there are
        any failures it will be either -1 (original value unchanged) or some value other than 0.

        :param vat_no: The vat number to lookup
        :return: Dictionary of result, initial value of keys are updated depending on error or success
        """

        # Dictionary values are false or null to start with and only updated on a successful lookup,
        # dictionary is passed to VAT lookup in each subsidiary module.
        # The ret_code is checked on return.
        self.result = {
            'ret_code': -1,
            'valid': False,
            'vat_enabled': False,
            'err_msg': None,
            'has_details': False,
            'company_name': None,
            'street': None,
            'postal_code': None,
            'city': None,
            'country_code': None,
            'country': None,
        }

        # Strip out spaces, dots, dashes and so forth. None of the online validators use them.
        self.vat_no = re.sub(r'[\W_]+', '', vat_no).upper()

        # Get the country code for lookup in dictionary and force the two character country code to uppercase
        # Check to see if country code is in the list of counties, if not fail and return error dict.
        self.country_code = vat_no[:2]
        if self.country_code not in self.countries:
            print(f"The country code, {self.country_code}, of the VAT number, {vat_no}, "
                  f"is not in the supported country VAT list.")
            self.result['err_msg'] = f"The country code, {self.country_code}, of the VAT number, " \
                                     f"{vat_no}, is not in the supported list of VAT countries."
            return self.result

        # Lookup the regex for the country VAT number format from the countries dict
        regex_pattern = self.countries[self.country_code]['rx']

        # The regex pattern has to be a raw string to escape characters like '\' which are used
        # everywhere in re, this used an f-string prefixed with 'r'.
        match = re.fullmatch(rf"{regex_pattern}", self.vat_no)

        if self.countries[self.country_code]['eu']:
            self.country_type = "EU country"
        else:
            self.country_type = "non-EU country"

        if match:
            print(f"\nThe VAT number, {vat_no}, matches the VAT number format for the {self.country_type}, "
                  f"{self.country_code}, {self.countries[self.country_code]['name']}.\n")
        else:
            print(f"The VAT number, {vat_no}, does NOT match the VAT number format for country {self.country_code}.\n")
            self.result['err_msg'] = f"The VAT number, {vat_no}, does NOT match the VAT number format " \
                                     f"for country {self.country_code}."
            return self.result

        # Step through lookups, if no lookup available advise.
        # EU country
        if self.countries[self.country_code]['eu']:
            # The new REST API service does not need a connection pre-check
            # # Try to connect to web service
            # try:
            #     self.lookup_eu_vat.connect()
            # except Exception as e:
            #     # If, after multiple Tenacity retry attempts, a connection to the web service cannot
            #     # be established no point in continuing.
            #     print(f"Connection to VIES service did not work, the error was:\n{e}")
            #     self.result['err_msg'] = f"Could not connect to service, error = {e}"
            #     return self.result

            # Try lookup(s)
            try:
                print(f"Looking up vat number {self.vat_no} using EU lookup service.")
                self.result.update(self.lookup_eu_vat.lookup_vat(self.vat_no, self.result))
            # Error, Zeep client was not assigned in check_eu.py, program cannot continue.
            except UnboundLocalError as e:
                self.result['err_msg'] = f"\nUnrecoverable error, '{e}', in SOAP module program will terminate.\n"
                return self.result
            # Final 'catch all' exception, SOAP services can be finicky. A case of how we might get here is
            # the VIES service is down and the WSDL is unavailable. Results in this error page if the WSDL URL is
            # navigated to — https://sorry.ec.europa.eu
            except Exception as e:
                print(f"\nUnrecoverable error, '{e}', program will terminate.\n")
                self.result['err_msg'] = f"{e.args[0]}"
                return self.result
            else:
                if self.result['valid']:
                    if self.result['country_code'] is None:
                        self.result['country_code'] = self.country_code
                    self.result['country'] = self.countries[self.result['country_code']]['name']
                    self.result['ret_code'] = 0
                return self.result

        # Switzerland
        elif self.country_code == 'CH':
            # Try to connect to web service.
            # We have to create a new connection for *each* lookup because of rate limiting restrictions
            # by the Swiss web service. The Zeep settings for the CH client are set to disable 'keep-alive'.
            try:
                self.lookup_ch_vat.connect()
            except Exception as e:
                print(f"\nTried multiple times to connect without success, the error was:\n{e}")
                self.result['err_msg'] = f"Could not connect to server, error = {e}"
                return self.result

            # Then try lookup
            try:
                print(f"Looking up vat number {self.vat_no} using CH lookup service.")
                self.result.update(self.lookup_ch_vat.lookup_vat(self.vat_no, self.result))
            # Error, Zeep client was not assigned in check_ch.py, program cannot continue.
            except UnboundLocalError as e:
                self.result['err_msg'] = f"Unrecoverable error, '{e}', program will terminate."
                return self.result
            except Exception as e:
                print(f"\nLookup process for Switzerland had an error that could not be recovered from.\n"
                      f"\tError = {e}")
                self.result['err_msg'] = f"Lookup failure, error = {e}"
                return self.result
            # No errors connecting to service
            else:
                # Get the actual country name from the country code of the address,
                # not the country code prefix of the VAT number.
                if self.result['valid']:
                    self.result['country'] = self.countries[self.result['country_code']]['name']
                    self.result['ret_code'] = 0
                return self.result

        # United Kingdom
        elif self.country_code == 'GB':
            # Not using SOAP, do not need to connect first
            try:
                print(f"Looking up vat number {self.vat_no} using UK lookup service.")
                self.result.update(self.lookup_uk_vat.lookup_vat(self.vat_no, self.result))
            except Exception as e:
                print(f"\nLookup process for the UK had an error that could not be recovered from.\n"
                      f"\tError = {e}")
                self.result['err_msg'] = f"Lookup failure, error = {e}"
                return self.result
            else:
                if self.result['valid']:
                    self.result['country'] = self.countries[self.result['country_code']]['name']
                    self.result['ret_code'] = 0
                return self.result

        # Norway
        elif self.country_code == 'NO':
            # Not using SOAP, do not need to connect first
            try:
                print(f"Looking up vat number {self.vat_no} using NO lookup service.")
                self.result.update(self.lookup_no_vat.lookup_vat(self.vat_no, self.result))
            except Exception as e:
                self.result['err_msg'] = f"{e}"
                return self.result
            else:
                if self.result['valid']:
                    self.result['country'] = self.countries[self.result['country_code']]['name']
                    self.result['ret_code'] = 0
                return self.result

        # We don't have code to do lookup for the country even though they are in the dict of countries.
        # In absence of validation as VAT number matches the VAT number set as valid and return.
        else:
            print(f"The country code {self.country_code} is valid, and the VAT number matches the format for the "
                  f"country, but there is currently no validation code available for this country.")
            self.result['valid'] = True
            self.result['err_msg'] = f"The country code {self.country_code} is valid, and the VAT number matches " \
                                     f"the format for the country, but there is currently no validation code " \
                                     f"available for this country."
            return self.result


def main():
    """
    Do single interactive lookup and validation of VAT number
    :return: None
    """

    banner = f'''\033[91m
        Welcome to...
        \033[94m
        ██╗   ██╗ █████╗ ████████╗     ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗███████╗██████╗ 
        ██║   ██║██╔══██╗╚══██╔══╝    ██╔════╝██║  ██║██╔════╝██╔════╝██║ ██╔╝██╔════╝██╔══██╗
        ██║   ██║███████║   ██║       ██║     ███████║█████╗  ██║     █████╔╝ █████╗  ██████╔╝
        ╚██╗ ██╔╝██╔══██║   ██║       ██║     ██╔══██║██╔══╝  ██║     ██╔═██╗ ██╔══╝  ██╔══██╗
         ╚████╔╝ ██║  ██║   ██║       ╚██████╗██║  ██║███████╗╚██████╗██║  ██╗███████╗██║  ██║
          ╚═══╝  ╚═╝  ╚═╝   ╚═╝        ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
        \033[00m'''

    print(banner)
    vat_no = input('Enter a VAT number to look up: ')
    # Create instance
    check = CheckVat()
    result = check.do_lookup(vat_no)

    if result['ret_code'] != 0:
        raise SystemExit(f"The VAT number lookup failed — see error message. Cancelling processing.\n"
                         f"\tError code: {result['ret_code']}\n"
                         f"\tError message: {result['err_msg']}")
    else:
        print(result)


if __name__ == '__main__':
    main()
