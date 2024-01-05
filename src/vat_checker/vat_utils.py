"""
General common use utilities
"""


def bitwise_op(value: int, bit_index: int, operation: int) -> int:
    """
    Perform bitwise twos compliment operations.
    Reference https://realpython.com/python-bitwise-operators/

    :param value: Integer being checked/changed
    :param bit_index: Uses standard Python zero-based indexing so to do a GET for the fifth index
                      location on INT 10000 / BIN 10011100010000 the bit index would be 4.
    :param operation: One of get | set | unset | flip, any other will return invalid.
    :return: An integer in all cases but with different values depending on the operation.
             For set and flip the whole number (value) with the operation performed is returned,
             for get either 0 or 1 is returned which can be used a BOOLEAN test.
    """
    GET: int = 0
    SET: int = 1
    UNSET: int = 2
    FLIP: int = 3
    INVALID: int = -1

    if operation == GET:
        return (value >> bit_index) & 1
    elif operation == SET:
        return value | (1 << bit_index)
    elif operation == UNSET:
        return value & ~(1 << bit_index)
    elif operation == FLIP:
        return value ^ (1 << bit_index)
    else:
        print(f"Requested operation, {operation}, is invalid.")
        return INVALID


def create_error_flags_dict() -> dict:
    """
    Standard error flags dictionary, doing it here to have one master copy location.
    The flags *cannot* change once the system goes production as historical records will
    have the flags set. Currently, it's 2 bytes, 16 bits, if it needs to grow I will add
    another byte (8 bits) to take it up to 3 bytes, 24 bits.
    :return: Dictionary of error flags
    """
    error_flags = {
        0: "Undetermined error - contact the system administrator.",
        1: "Invalid/missing distributor ID.",
        2: "Invalid/missing reseller ID.",
        3: "Invalid/missing VAT number.",
        4: "Invalid/missing item number.",
        5: "Invalid/missing currency ID.",
        6: "Transaction date missing, in the future, or significantly in the past.",
        7: "Invalid/missing quantity, or equals zero.",
        8: "Missing sales amount, or equals zero.",
        9: "Negative/positive sign of quantity does not match amount.",
        10: "Duplicate Salesforce account, correct in Salesforce.",
        11: "Salesforce account problem, existing account issue, or new account creation failed.",
        12: "Mapping data problem - contact the system administrator.",
        13: "DRP account problem, new account creation failed - contact the system administrator.",
        14: "Unassigned, not in use.",
        15: "Upload to Sales Portal failed - contact the system administrator.",
    }
    return error_flags


def get_error_flags_list(error_flag):
    error_flags = create_error_flags_dict()
    if not isinstance(error_flag, int):
        print(f"Error flag supplied, {error_flag}, is not an integer.")
        return False
    else:
        if 1 <= error_flag <= 65535:
            # Reassemble it
            error_list = ''
            # Range has to be one beyond the desired integer as Python is zero based
            for n in range(16):
                # Get flag as single bit and shift right
                f = error_flag >> n & 1
                # Use 0/1 from bit value for false/true
                if f:
                    error_list = error_list + error_flags[n] + ' + '
            # Remove trailing ' + '
            error_list = error_list[:-3]
            print(f"\nError flag in binary: {format(error_flag, '#018b')}")
            return error_list
        else:
            print(f"Error flag value {error_flag} is out of range, must be between 1 and 65,535")
            return False


def get_country_vat_number_formats() -> dict:
    country_vats = {
        'AT': r'ATU\d{8}',
        'BE': r'BE(0|1)\d{9}',
        'BG': r'BG\d{9,10}',
        'CH': r'CHE\d{9}',
        'CY': r'CY\d{8}[A-Z]',
        'CZ': r'CZ\d{8,10}',
        'DE': r'DE\d{9}',
        'DK': r'DK\d{8}',
        'EE': r'EE\d{9}',
        'EL': r'EL\d{9}',
        # 'ES': 'ES[A-Z]\d{8}|ES\d{8}[A-Z]|ES[A-Z]\d{7}[A-Z]',
        'ES': r'ES.{9}',
        'FI': r'FI\d{8}',
        'FR': r'FR\d{11}|(((([A-H]|[J-N]|[P-Z])\d)|(\d([A-H]|[J-N]|[P-Z])))\d{9})|[^OI]{2}\d{9}',
        'GB': r'GB\d{9}',
        'HR': r'HR\d{11}',
        'HU': r'HU\d{8}',
        'IE': r'IE\d{7}[A-Z]|\d[A-Z]\d{5}[A-Z]',
        'IT': r'IT\d{11}',
        'LI': r'LI\d{5}',
        'LT': r'LT\d{9}(\d{3})?',
        'LU': r'LU\d{8}',
        'LV': r'LV\d{11}',
        'MT': r'MT\d{8}',
        'NL': r'NL\d{9}B\d{2}',
        'NO': r'NO\d{9}',
        'PL': r'PL\d{10}',
        'PT': r'PT\d{9}',
        'RO': r'RO\d{2,10}',
        'RS': r'RS\d{9}',
        'SE': r'SE\d{12}',
        'SI': r'SI\d{8}',
        'SK': r'SK\d{10}',
        'SM': r'SM\d{5}',
        'XI': r'XI\d{9}',
    }
    return country_vats


def get_euro_currencies() -> list:
    euro_currencies = ["ALL", "AMD", "AZN", "BAM", "BGN", "BYN", "CHF", "CZK", "DKK", "EUR", "GBP", "GEL",
                       "GGP", "GIP", "HRK", "HUF", "IMP", "ISK", "JEP", "KZT", "MDL", "MKD", "NOK", "PLN",
                       "RON", "RSD", "RUB", "RUE", "SEK", "UAH"]
    return euro_currencies


def get_country_currency() -> dict:
    """
    Build dictionary of currencies of European countries
    :return: dictionary
    """
    currencies = {
        "AX": "EUR",
        "AL": "ALL",
        "AD": "EUR",
        "AM": "AMD",
        "AT": "EUR",
        "AZ": "AZN",
        "BY": "BYN",
        "BE": "EUR",
        "BA": "BAM",
        "BG": "BGN",
        "HR": "HRK",
        "CY": "EUR",
        "CZ": "CZK",
        "DK": "DKK",
        "EE": "RUE",
        "ES": "EUR",
        "FO": "DKK",
        "FI": "EUR",
        "FR": "EUR",
        "GF": "XXX",
        "PF": "XXX",
        "TF": "XXX",
        "GE": "GEL",
        "DE": "EUR",
        "GB": "GBP",
        "GI": "GIP",
        "GR": "EUR",
        "GL": "DKK",
        "GG": "GGP",
        "HU": "HUF",
        "IS": "ISK",
        "IE": "EUR",
        "IM": "IMP",
        "IT": "EUR",
        "JE": "JEP",
        "KZ": "KZT",
        "LV": "EUR",
        "LI": "CHF",
        "LT": "EUR",
        "LU": "EUR",
        "MK": "MKD",
        "MT": "EUR",
        "MD": "MDL",
        "MC": "EUR",
        "ME": "EUR",
        "NL": "EUR",
        "NO": "NOK",
        "PL": "PLN",
        "PT": "EUR",
        "RO": "RON",
        "RU": "RUB",
        "SM": "EUR",
        "RS": "RSD",
        "SK": "EUR",
        "SI": "EUR",
        "SJ": "NOK",
        "SE": "SEK",
        "CH": "CHF",
        "UA": "UAH",
        "VA": "EUR",
    }
    return currencies


def get_country_code_from_name() -> dict:
    country_names = {
        "afghanistan": "AF", "åland islands": "AX", "albania": "AL", "algeria": "DZ", "american samoa": "AS",
        "andorra": "AD", "angola": "AO", "anguilla": "AI", "antarctica": "AQ", "antigua and barbuda": "AG",
        "argentina": "AR", "armenia": "AM", "aruba": "AW", "australia": "AU", "austria": "AT", "azerbaijan": "AZ",
        "bahamas": "BS", "bahrain": "BH", "bangladesh": "BD", "barbados": "BB", "belarus": "BY", "belgium": "BE",
        "belize": "BZ", "benin": "BJ", "bermuda": "BM", "bhutan": "BT", "bolivia": "BO",
        "sint eustatius and saba bonaire": "BQ", "bosnia and herzegovina": "BA", "botswana": "BW",
        "bouvet island": "BV", "brazil": "BR", "british indian ocean territory": "IO", "brunei darussalam": "BN",
        "bulgaria": "BG", "burkina faso": "BF", "burundi": "BI", "cambodia": "KH", "cameroon": "CM", "canada": "CA",
        "cape verde": "CV", "cayman islands": "KY", "central african republic": "CF", "chad": "TD", "chile": "CL",
        "china": "CN", "christmas island": "CX", "cocos (keeling) islands": "CC", "colombia": "CO", "comoros": "KM",
        "congo": "CG", "democratic republic of the congo": "CD", "cook islands": "CK", "costa rica": "CR",
        "côte d'ivoire": "CI", "croatia": "HR", "cuba": "CU", "curaçao": "CW", "cyprus": "CY", "czech republic": "CZ",
        "denmark": "DK", "djibouti": "DJ", "dominica": "DM", "dominican republic": "DO", "ecuador": "EC", "egypt": "EG",
        "el salvador": "SV", "equatorial guinea": "GQ", "eritrea": "ER", "estonia": "EE", "ethiopia": "ET",
        "falkland islands": "FK", "faroe islands": "FO", "fiji": "FJ", "finland": "FI", "france": "FR",
        "french guiana": "GF", "french polynesia": "PF", "french southern territories": "TF", "gabon": "GA",
        "gambia": "GM", "georgia": "GE", "germany": "DE", "ghana": "GH", "gibraltar": "GI", "greece": "GR",
        "greenland": "GL", "grenada": "GD", "guadeloupe": "GP", "guam": "GU", "guatemala": "GT", "guernsey": "GG",
        "guinea": "GN", "guinea-bissau": "GW", "guyana": "GY", "haiti": "HT", "heard island and mcdonald islands": "HM",
        "vatican city state": "VA", "honduras": "HN", "hong kong": "HK", "hungary": "HU", "iceland": "IS",
        "india": "IN", "indonesia": "ID", "iran": "IR", "iraq": "IQ", "ireland": "IE", "isle of man": "IM",
        "israel": "IL", "italy": "IT", "jamaica": "JM", "japan": "JP", "jersey": "JE", "jordan": "JO",
        "kazakhstan": "KZ", "kenya": "KE", "kiribati": "KI", "democratic people's republic of korea": "KP",
        "republic of korea": "KR", "kuwait": "KW", "kyrgyzstan": "KG", "lao people's democratic republic": "LA",
        "latvia": "LV", "lebanon": "LB", "lesotho": "LS", "liberia": "LR", "libya": "LY", "liechtenstein": "LI",
        "lithuania": "LT", "luxembourg": "LU", "macao": "MO", "macedonia": "MK", "madagascar": "MG", "malawi": "MW",
        "malaysia": "MY", "maldives": "MV", "mali": "ML", "malta": "MT", "marshall islands": "MH", "martinique": "MQ",
        "mauritania": "MR", "mauritius": "MU", "mayotte": "YT", "mexico": "MX", "federated states of micronesia": "FM",
        "moldova": "MD", "monaco": "MC", "mongolia": "MN", "montenegro": "ME", "montserrat": "MS", "morocco": "MA",
        "mozambique": "MZ", "myanmar": "MM", "namibia": "NA", "nauru": "NR", "nepal": "NP", "netherlands": "NL",
        "new caledonia": "NC", "new zealand": "NZ", "nicaragua": "NI", "niger": "NE", "nigeria": "NG", "niue": "NU",
        "norfolk island": "NF", "northern mariana islands": "MP", "norway": "NO", "oman": "OM", "pakistan": "PK",
        "palau": "PW", "panama": "PA", "papua new guinea": "PG", "paraguay": "PY", "peru": "PE", "philippines": "PH",
        "pitcairn": "PN", "poland": "PL", "portugal": "PT", "puerto rico": "PR", "qatar": "QA", "réunion": "RE",
        "romania": "RO", "russian federation": "RU", "rwanda": "RW", "saint barthélemy": "BL", "saint helena": "SH",
        "saint kitts and nevis": "KN", "saint lucia": "LC", "saint martin": "MF", "saint pierre and miquelon": "PM",
        "saint vincent and the grenadines": "VC", "samoa": "WS", "san marino": "SM", "sao tome and principe": "ST",
        "saudi arabia": "SA", "senegal": "SN", "serbia": "RS", "seychelles": "SC", "sierra leone": "SL",
        "singapore": "SG", "sint maarten": "SX", "slovakia": "SK", "slovenia": "SI", "solomon islands": "SB",
        "somalia": "SO", "south africa": "ZA", "south georgia and the south sandwich islands": "GS",
        "south sudan": "SS", "spain": "ES", "sri lanka": "LK", "sudan": "SD", "suriname": "SR",
        "svalbard and jan mayen": "SJ", "swaziland": "SZ", "sweden": "SE", "switzerland": "CH",
        "syrian arab republic": "SY", "taiwan": "TW", "tajikistan": "TJ", "tanzania": "TZ", "thailand": "TH",
        "timor-leste": "TL", "togo": "TG", "tokelau": "TK", "tonga": "TO", "trinidad and tobago": "TT", "tunisia": "TN",
        "turkey": "TR", "turkmenistan": "TM", "turks and caicos islands": "TC", "tuvalu": "TV", "uganda": "UG",
        "ukraine": "UA", "united arab emirates": "AE", "united kingdom": "GB", "united states": "US",
        "united states minor outlying islands": "UM", "uruguay": "UY", "uzbekistan": "UZ", "vanuatu": "VU",
        "venezuela": "VE", "viet nam": "VN", "virgin islands, british": "VG", "virgin islands, u.s.": "VI",
        "wallis and futuna": "WF", "western sahara": "EH", "yemen": "YE", "zambia": "ZM", "zimbabwe": "ZW",
    }
    return country_names


def get_country_name_from_code() -> dict:
    country_codes = {
        "AF": "Afghanistan", "AX": "Åland Islands", "AL": "Albania", "DZ": "Algeria", "AS": "American Samoa",
        "AD": "Andorra", "AO": "Angola", "AI": "Anguilla", "AQ": "Antarctica", "AG": "Antigua and Barbuda",
        "AR": "Argentina", "AM": "Armenia", "AW": "Aruba", "AU": "Australia", "AT": "Austria", "AZ": "Azerbaijan",
        "BS": "Bahamas", "BH": "Bahrain", "BD": "Bangladesh", "BB": "Barbados", "BY": "Belarus", "BE": "Belgium",
        "BZ": "Belize", "BJ": "Benin", "BM": "Bermuda", "BT": "Bhutan", "BO": "Bolivia",
        "BQ": "Sint Eustatius and Saba Bonaire", "BA": "Bosnia and Herzegovina", "BW": "Botswana",
        "BV": "Bouvet Island", "BR": "Brazil", "IO": "British Indian Ocean Territory", "BN": "Brunei Darussalam",
        "BG": "Bulgaria", "BF": "Burkina Faso", "BI": "Burundi", "KH": "Cambodia", "CM": "Cameroon", "CA": "Canada",
        "CV": "Cape Verde", "KY": "Cayman Islands", "CF": "Central African Republic", "TD": "Chad", "CL": "Chile",
        "CN": "China", "CX": "Christmas Island", "CC": "Cocos (Keeling) Islands", "CO": "Colombia", "KM": "Comoros",
        "CG": "Congo", "CD": "Democratic Republic of the Congo", "CK": "Cook Islands", "CR": "Costa Rica",
        "CI": "Côte d'Ivoire", "HR": "Croatia", "CU": "Cuba", "CW": "Curaçao", "CY": "Cyprus", "CZ": "Czech Republic",
        "DK": "Denmark", "DJ": "Djibouti", "DM": "Dominica", "DO": "Dominican Republic", "EC": "Ecuador", "EG": "Egypt",
        "SV": "El Salvador", "GQ": "Equatorial Guinea", "ER": "Eritrea", "EE": "Estonia", "ET": "Ethiopia",
        "FK": "Falkland Islands", "FO": "Faroe Islands", "FJ": "Fiji", "FI": "Finland", "FR": "France",
        "GF": "French Guiana", "PF": "French Polynesia", "TF": "French Southern Territories", "GA": "Gabon",
        "GM": "Gambia", "GE": "Georgia", "DE": "Germany", "GH": "Ghana", "GI": "Gibraltar", "GR": "Greece",
        "GL": "Greenland", "GD": "Grenada", "GP": "Guadeloupe", "GU": "Guam", "GT": "Guatemala", "GG": "Guernsey",
        "GN": "Guinea", "GW": "Guinea-Bissau", "GY": "Guyana", "HT": "Haiti", "HM": "Heard Island and McDonald Islands",
        "VA": "Vatican City State", "HN": "Honduras", "HK": "Hong Kong", "HU": "Hungary", "IS": "Iceland",
        "IN": "India", "ID": "Indonesia", "IR": "Iran", "IQ": "Iraq", "IE": "Ireland", "IM": "Isle of Man",
        "IL": "Israel", "IT": "Italy", "JM": "Jamaica", "JP": "Japan", "JE": "Jersey", "JO": "Jordan",
        "KZ": "Kazakhstan", "KE": "Kenya", "KI": "Kiribati", "KP": "Democratic People's Republic of Korea",
        "KR": "Republic of Korea", "KW": "Kuwait", "KG": "Kyrgyzstan", "LA": "Lao People's Democratic Republic",
        "LV": "Latvia", "LB": "Lebanon", "LS": "Lesotho", "LR": "Liberia", "LY": "Libya", "LI": "Liechtenstein",
        "LT": "Lithuania", "LU": "Luxembourg", "MO": "Macao", "MK": "Macedonia", "MG": "Madagascar", "MW": "Malawi",
        "MY": "Malaysia", "MV": "Maldives", "ML": "Mali", "MT": "Malta", "MH": "Marshall Islands", "MQ": "Martinique",
        "MR": "Mauritania", "MU": "Mauritius", "YT": "Mayotte", "MX": "Mexico", "FM": "Federated States of Micronesia",
        "MD": "Moldova", "MC": "Monaco", "MN": "Mongolia", "ME": "Montenegro", "MS": "Montserrat", "MA": "Morocco",
        "MZ": "Mozambique", "MM": "Myanmar", "NA": "Namibia", "NR": "Nauru", "NP": "Nepal", "NL": "Netherlands",
        "NC": "New Caledonia", "NZ": "New Zealand", "NI": "Nicaragua", "NE": "Niger", "NG": "Nigeria", "NU": "Niue",
        "NF": "Norfolk Island", "MP": "Northern Mariana Islands", "NO": "Norway", "OM": "Oman", "PK": "Pakistan",
        "PW": "Palau", "PA": "Panama", "PG": "Papua New Guinea", "PY": "Paraguay", "PE": "Peru", "PH": "Philippines",
        "PN": "Pitcairn", "PL": "Poland", "PT": "Portugal", "PR": "Puerto Rico", "QA": "Qatar", "RE": "Réunion",
        "RO": "Romania", "RU": "Russian Federation", "RW": "Rwanda", "BL": "Saint Barthélemy", "SH": "Saint Helena",
        "KN": "Saint Kitts and Nevis", "LC": "Saint Lucia", "MF": "Saint Martin", "PM": "Saint Pierre and Miquelon",
        "VC": "Saint Vincent and the Grenadines", "WS": "Samoa", "SM": "San Marino", "ST": "Sao Tome and Principe",
        "SA": "Saudi Arabia", "SN": "Senegal", "RS": "Serbia", "SC": "Seychelles", "SL": "Sierra Leone",
        "SG": "Singapore", "SX": "Sint Maarten", "SK": "Slovakia", "SI": "Slovenia", "SB": "Solomon Islands",
        "SO": "Somalia", "ZA": "South Africa", "GS": "South Georgia and the South Sandwich Islands",
        "SS": "South Sudan", "ES": "Spain", "LK": "Sri Lanka", "SD": "Sudan", "SR": "Suriname",
        "SJ": "Svalbard and Jan Mayen", "SZ": "Swaziland", "SE": "Sweden", "CH": "Switzerland",
        "SY": "Syrian Arab Republic", "TW": "Taiwan", "TJ": "Tajikistan", "TZ": "Tanzania", "TH": "Thailand",
        "TL": "Timor-Leste", "TG": "Togo", "TK": "Tokelau", "TO": "Tonga", "TT": "Trinidad and Tobago", "TN": "Tunisia",
        "TR": "Turkey", "TM": "Turkmenistan", "TC": "Turks and Caicos Islands", "TV": "Tuvalu", "UG": "Uganda",
        "UA": "Ukraine", "AE": "United Arab Emirates", "GB": "United Kingdom", "US": "United States",
        "UM": "United States Minor Outlying Islands", "UY": "Uruguay", "UZ": "Uzbekistan", "VU": "Vanuatu",
        "VE": "Venezuela", "VN": "Viet Nam", "VG": "Virgin Islands, British", "VI": "Virgin Islands, U.S.",
        "WF": "Wallis and Futuna", "EH": "Western Sahara", "YE": "Yemen", "ZM": "Zambia", "ZW": "Zimbabwe",
    }
    return country_codes


def main():
    print("You shouldn't be here")
    error_flag = 2048
    if bitwise_op(error_flag, 3, 0):
        print(f"Flag {error_flag} is set")
    else:
        print(f"Flag {error_flag} is not set")
    error_flag = bitwise_op(error_flag, 3, 1)
    print(error_flag)
    error_flag = bitwise_op(error_flag, 3, 2)
    print(error_flag)


if __name__ == '__main__':
    main()
