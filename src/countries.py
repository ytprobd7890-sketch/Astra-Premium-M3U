"""ISO 3166-1 country codes with English and Bangla names.

Bangla names are curated for the countries that appear as stream-server
origins; the remaining ISO-3166 codes keep their English short name, so a
playlist never shows a bare two-letter code in the player.
"""

# code: (English short name, Bangla name)
COUNTRIES = {
    'AD': ('Andorra', 'Andorra'),
    'AE': ('United Arab Emirates', 'সংযুক্ত আরব আমিরাত'),
    'AF': ('Afghanistan', 'আফগানিস্তান'),
    'AG': ('Antigua and Barbuda', 'Antigua and Barbuda'),
    'AI': ('Anguilla', 'Anguilla'),
    'AL': ('Albania', 'আলবেনিয়া'),
    'AM': ('Armenia', 'আর্মেনিয়া'),
    'AO': ('Angola', 'অ্যাঙ্গোলা'),
    'AQ': ('Antarctica', 'Antarctica'),
    'AR': ('Argentina', 'আর্জেন্টিনা'),
    'AS': ('American Samoa', 'American Samoa'),
    'AT': ('Austria', 'অস্ট্রিয়া'),
    'AU': ('Australia', 'অস্ট্রেলিয়া'),
    'AW': ('Aruba', 'Aruba'),
    'AX': ('Åland Islands', 'Åland Islands'),
    'AZ': ('Azerbaijan', 'আজারবাইজান'),
    'BA': ('Bosnia and Herzegovina', 'বসনিয়া ও হার্জেগোভিনা'),
    'BB': ('Barbados', 'বার্বাডোস'),
    'BD': ('Bangladesh', 'বাংলাদেশ'),
    'BE': ('Belgium', 'বেলজিয়াম'),
    'BF': ('Burkina Faso', 'Burkina Faso'),
    'BG': ('Bulgaria', 'বুলগেরিয়া'),
    'BH': ('Bahrain', 'বাহরাইন'),
    'BI': ('Burundi', 'Burundi'),
    'BJ': ('Benin', 'Benin'),
    'BL': ('Saint Barthélemy', 'Saint Barthélemy'),
    'BM': ('Bermuda', 'Bermuda'),
    'BN': ('Brunei Darussalam', 'ব্রুনাই'),
    'BO': ('Bolivia, Plurinational State of', 'বলিভিয়া'),
    'BQ': ('Bonaire, Sint Eustatius and Saba', 'Bonaire, Sint Eustatius and Saba'),
    'BR': ('Brazil', 'ব্রাজিল'),
    'BS': ('Bahamas', 'বাহামা'),
    'BT': ('Bhutan', 'ভুটান'),
    'BV': ('Bouvet Island', 'Bouvet Island'),
    'BW': ('Botswana', 'বতসোয়ানা'),
    'BY': ('Belarus', 'বেলারুশ'),
    'BZ': ('Belize', 'বেলিজ'),
    'CA': ('Canada', 'কানাডা'),
    'CC': ('Cocos (Keeling) Islands', 'Cocos (Keeling) Islands'),
    'CD': ('Congo, The Democratic Republic of the', 'Congo, The Democratic Republic of the'),
    'CF': ('Central African Republic', 'Central African Republic'),
    'CG': ('Congo', 'Congo'),
    'CH': ('Switzerland', 'সুইজারল্যান্ড'),
    'CI': ("Côte d'Ivoire", 'আইভরি কোস্ট'),
    'CK': ('Cook Islands', 'Cook Islands'),
    'CL': ('Chile', 'চিলি'),
    'CM': ('Cameroon', 'ক্যামেরুন'),
    'CN': ('China', 'চীন'),
    'CO': ('Colombia', 'কলম্বিয়া'),
    'CR': ('Costa Rica', 'কোস্টারিকা'),
    'CU': ('Cuba', 'কিউবা'),
    'CV': ('Cabo Verde', 'Cabo Verde'),
    'CW': ('Curaçao', 'Curaçao'),
    'CX': ('Christmas Island', 'Christmas Island'),
    'CY': ('Cyprus', 'সাইপ্রাস'),
    'CZ': ('Czechia', 'চেকিয়া'),
    'DE': ('Germany', 'জার্মানি'),
    'DJ': ('Djibouti', 'Djibouti'),
    'DK': ('Denmark', 'ডেনমার্ক'),
    'DM': ('Dominica', 'Dominica'),
    'DO': ('Dominican Republic', 'ডোমিনিকান প্রজাতন্ত্র'),
    'DZ': ('Algeria', 'আলজেরিয়া'),
    'EC': ('Ecuador', 'ইকুয়েডর'),
    'EE': ('Estonia', 'এস্তোনিয়া'),
    'EG': ('Egypt', 'মিশর'),
    'EH': ('Western Sahara', 'Western Sahara'),
    'ER': ('Eritrea', 'Eritrea'),
    'ES': ('Spain', 'স্পেন'),
    'ET': ('Ethiopia', 'ইথিওপিয়া'),
    'FI': ('Finland', 'ফিনল্যান্ড'),
    'FJ': ('Fiji', 'ফিজি'),
    'FK': ('Falkland Islands (Malvinas)', 'Falkland Islands (Malvinas)'),
    'FM': ('Micronesia, Federated States of', 'Micronesia, Federated States of'),
    'FO': ('Faroe Islands', 'Faroe Islands'),
    'FR': ('France', 'ফ্রান্স'),
    'GA': ('Gabon', 'Gabon'),
    'GB': ('United Kingdom', 'যুক্তরাজ্য'),
    'GD': ('Grenada', 'Grenada'),
    'GE': ('Georgia', 'জর্জিয়া'),
    'GF': ('French Guiana', 'French Guiana'),
    'GG': ('Guernsey', 'Guernsey'),
    'GH': ('Ghana', 'ঘানা'),
    'GI': ('Gibraltar', 'Gibraltar'),
    'GL': ('Greenland', 'Greenland'),
    'GM': ('Gambia', 'Gambia'),
    'GN': ('Guinea', 'Guinea'),
    'GP': ('Guadeloupe', 'Guadeloupe'),
    'GQ': ('Equatorial Guinea', 'Equatorial Guinea'),
    'GR': ('Greece', 'গ্রিস'),
    'GS': ('South Georgia and the South Sandwich Islands', 'South Georgia and the South Sandwich Islands'),
    'GT': ('Guatemala', 'গুয়াতেমালা'),
    'GU': ('Guam', 'Guam'),
    'GW': ('Guinea-Bissau', 'Guinea-Bissau'),
    'GY': ('Guyana', 'গায়ানা'),
    'HK': ('Hong Kong', 'হংকং'),
    'HM': ('Heard Island and McDonald Islands', 'Heard Island and McDonald Islands'),
    'HN': ('Honduras', 'হন্ডুরাস'),
    'HR': ('Croatia', 'ক্রোয়েশিয়া'),
    'HT': ('Haiti', 'হাইতি'),
    'HU': ('Hungary', 'হাঙ্গেরি'),
    'ID': ('Indonesia', 'ইন্দোনেশিয়া'),
    'IE': ('Ireland', 'আয়ারল্যান্ড'),
    'IL': ('Israel', 'ইসরায়েল'),
    'IM': ('Isle of Man', 'Isle of Man'),
    'IN': ('India', 'ভারত'),
    'IO': ('British Indian Ocean Territory', 'British Indian Ocean Territory'),
    'IQ': ('Iraq', 'ইরাক'),
    'IR': ('Iran, Islamic Republic of', 'ইরান'),
    'IS': ('Iceland', 'আইসল্যান্ড'),
    'IT': ('Italy', 'ইতালি'),
    'JE': ('Jersey', 'Jersey'),
    'JM': ('Jamaica', 'জ্যামাইকা'),
    'JO': ('Jordan', 'জর্ডান'),
    'JP': ('Japan', 'জাপান'),
    'KE': ('Kenya', 'কেনিয়া'),
    'KG': ('Kyrgyzstan', 'কিরগিজস্তান'),
    'KH': ('Cambodia', 'কম্বোডিয়া'),
    'KI': ('Kiribati', 'Kiribati'),
    'KM': ('Comoros', 'Comoros'),
    'KN': ('Saint Kitts and Nevis', 'Saint Kitts and Nevis'),
    'KP': ("Korea, Democratic People's Republic of", 'উত্তর কোরিয়া'),
    'KR': ('Korea, Republic of', 'দক্ষিণ কোরিয়া'),
    'KW': ('Kuwait', 'কুয়েত'),
    'KY': ('Cayman Islands', 'Cayman Islands'),
    'KZ': ('Kazakhstan', 'কাজাখস্তান'),
    'LA': ("Lao People's Democratic Republic", 'লাওস'),
    'LB': ('Lebanon', 'লেবানন'),
    'LC': ('Saint Lucia', 'Saint Lucia'),
    'LI': ('Liechtenstein', 'Liechtenstein'),
    'LK': ('Sri Lanka', 'শ্রীলঙ্কা'),
    'LR': ('Liberia', 'Liberia'),
    'LS': ('Lesotho', 'Lesotho'),
    'LT': ('Lithuania', 'লিথুয়ানিয়া'),
    'LU': ('Luxembourg', 'লুক্সেমবার্গ'),
    'LV': ('Latvia', 'লাটভিয়া'),
    'LY': ('Libya', 'লিবিয়া'),
    'MA': ('Morocco', 'মরক্কো'),
    'MC': ('Monaco', 'Monaco'),
    'MD': ('Moldova, Republic of', 'মলদোভা'),
    'ME': ('Montenegro', 'মন্টিনিগ্রো'),
    'MF': ('Saint Martin (French part)', 'Saint Martin (French part)'),
    'MG': ('Madagascar', 'মাদাগাস্কার'),
    'MH': ('Marshall Islands', 'Marshall Islands'),
    'MK': ('North Macedonia', 'উত্তর মেসিডোনিয়া'),
    'ML': ('Mali', 'মালি'),
    'MM': ('Myanmar', 'মিয়ানমার'),
    'MN': ('Mongolia', 'মঙ্গোলিয়া'),
    'MO': ('Macao', 'মাকাও'),
    'MP': ('Northern Mariana Islands', 'Northern Mariana Islands'),
    'MQ': ('Martinique', 'Martinique'),
    'MR': ('Mauritania', 'Mauritania'),
    'MS': ('Montserrat', 'Montserrat'),
    'MT': ('Malta', 'মাল্টা'),
    'MU': ('Mauritius', 'মরিশাস'),
    'MV': ('Maldives', 'মালদ্বীপ'),
    'MW': ('Malawi', 'Malawi'),
    'MX': ('Mexico', 'মেক্সিকো'),
    'MY': ('Malaysia', 'মালয়েশিয়া'),
    'MZ': ('Mozambique', 'মোজাম্বিক'),
    'NA': ('Namibia', 'নামিবিয়া'),
    'NC': ('New Caledonia', 'New Caledonia'),
    'NE': ('Niger', 'Niger'),
    'NF': ('Norfolk Island', 'Norfolk Island'),
    'NG': ('Nigeria', 'নাইজেরিয়া'),
    'NI': ('Nicaragua', 'নিকারাগুয়া'),
    'NL': ('Netherlands', 'নেদারল্যান্ডস'),
    'NO': ('Norway', 'নরওয়ে'),
    'NP': ('Nepal', 'নেপাল'),
    'NR': ('Nauru', 'Nauru'),
    'NU': ('Niue', 'Niue'),
    'NZ': ('New Zealand', 'নিউজিল্যান্ড'),
    'OM': ('Oman', 'ওমান'),
    'PA': ('Panama', 'পানামা'),
    'PE': ('Peru', 'পেরু'),
    'PF': ('French Polynesia', 'French Polynesia'),
    'PG': ('Papua New Guinea', 'পাপুয়া নিউগিনি'),
    'PH': ('Philippines', 'ফিলিপাইন'),
    'PK': ('Pakistan', 'পাকিস্তান'),
    'PL': ('Poland', 'পোল্যান্ড'),
    'PM': ('Saint Pierre and Miquelon', 'Saint Pierre and Miquelon'),
    'PN': ('Pitcairn', 'Pitcairn'),
    'PR': ('Puerto Rico', 'পুয়ের্তো রিকো'),
    'PS': ('Palestine, State of', 'ফিলিস্তিন'),
    'PT': ('Portugal', 'পর্তুগাল'),
    'PW': ('Palau', 'Palau'),
    'PY': ('Paraguay', 'প্যারাগুয়ে'),
    'QA': ('Qatar', 'কাতার'),
    'RE': ('Réunion', 'Réunion'),
    'RO': ('Romania', 'রোমানিয়া'),
    'RS': ('Serbia', 'সার্বিয়া'),
    'RU': ('Russian Federation', 'রাশিয়া'),
    'RW': ('Rwanda', 'রুয়ান্ডা'),
    'SA': ('Saudi Arabia', 'সৌদি আরব'),
    'SB': ('Solomon Islands', 'Solomon Islands'),
    'SC': ('Seychelles', 'Seychelles'),
    'SD': ('Sudan', 'সুদান'),
    'SE': ('Sweden', 'সুইডেন'),
    'SG': ('Singapore', 'সিঙ্গাপুর'),
    'SH': ('Saint Helena, Ascension and Tristan da Cunha', 'Saint Helena, Ascension and Tristan da Cunha'),
    'SI': ('Slovenia', 'স্লোভেনিয়া'),
    'SJ': ('Svalbard and Jan Mayen', 'Svalbard and Jan Mayen'),
    'SK': ('Slovakia', 'স্লোভাকিয়া'),
    'SL': ('Sierra Leone', 'Sierra Leone'),
    'SM': ('San Marino', 'San Marino'),
    'SN': ('Senegal', 'সেনেগাল'),
    'SO': ('Somalia', 'সোমালিয়া'),
    'SR': ('Suriname', 'সুরিনাম'),
    'SS': ('South Sudan', 'দক্ষিণ সুদান'),
    'ST': ('Sao Tome and Principe', 'Sao Tome and Principe'),
    'SV': ('El Salvador', 'এল সালভাদর'),
    'SX': ('Sint Maarten (Dutch part)', 'Sint Maarten (Dutch part)'),
    'SY': ('Syrian Arab Republic', 'সিরিয়া'),
    'SZ': ('Eswatini', 'Eswatini'),
    'TC': ('Turks and Caicos Islands', 'Turks and Caicos Islands'),
    'TD': ('Chad', 'Chad'),
    'TF': ('French Southern Territories', 'French Southern Territories'),
    'TG': ('Togo', 'Togo'),
    'TH': ('Thailand', 'থাইল্যান্ড'),
    'TJ': ('Tajikistan', 'তাজিকিস্তান'),
    'TK': ('Tokelau', 'Tokelau'),
    'TL': ('Timor-Leste', 'Timor-Leste'),
    'TM': ('Turkmenistan', 'তুর্কমেনিস্তান'),
    'TN': ('Tunisia', 'তিউনিসিয়া'),
    'TO': ('Tonga', 'Tonga'),
    'TR': ('Türkiye', 'তুরস্ক'),
    'TT': ('Trinidad and Tobago', 'ত্রিনিদাদ ও টোবাগো'),
    'TV': ('Tuvalu', 'Tuvalu'),
    'TW': ('Taiwan, Province of China', 'তাইওয়ান'),
    'TZ': ('Tanzania, United Republic of', 'তানজানিয়া'),
    'UA': ('Ukraine', 'ইউক্রেইন'),
    'UG': ('Uganda', 'উগান্ডা'),
    'UM': ('United States Minor Outlying Islands', 'United States Minor Outlying Islands'),
    'US': ('United States', 'মার্কিন যুক্তরাষ্ট্র'),
    'UY': ('Uruguay', 'উরুগুয়ে'),
    'UZ': ('Uzbekistan', 'উজবেকিস্তান'),
    'VA': ('Holy See (Vatican City State)', 'Holy See (Vatican City State)'),
    'VC': ('Saint Vincent and the Grenadines', 'Saint Vincent and the Grenadines'),
    'VE': ('Venezuela, Bolivarian Republic of', 'ভেনেজুয়েলা'),
    'VG': ('Virgin Islands, British', 'Virgin Islands, British'),
    'VI': ('Virgin Islands, U.S.', 'Virgin Islands, U.S.'),
    'VN': ('Viet Nam', 'ভিয়েতনাম'),
    'VU': ('Vanuatu', 'Vanuatu'),
    'WF': ('Wallis and Futuna', 'Wallis and Futuna'),
    'WS': ('Samoa', 'Samoa'),
    'YE': ('Yemen', 'ইয়েমেন'),
    'YT': ('Mayotte', 'Mayotte'),
    'ZA': ('South Africa', 'দক্ষিণ আফ্রিকা'),
    'ZM': ('Zambia', 'জাম্বিয়া'),
    'ZW': ('Zimbabwe', 'জিম্বাবুয়ে'),
}

# Used when a server IP is private, reserved, or simply not in the index.
UNKNOWN_CODE = 'XX'
UNKNOWN = ('Unknown', 'অজানা সার্ভার')

# Countries pinned to the top of every country-ordered playlist.
PINNED = ('BD',)


def country_name(code):
    """Return the Bangla name, falling back to the English name then the code."""
    if code == UNKNOWN_CODE:
        return UNKNOWN[1]
    names = COUNTRIES.get(code)
    return names[1] if names else code


def country_english_name(code):
    """Return the English short name, falling back to the code."""
    if code == UNKNOWN_CODE:
        return UNKNOWN[0]
    names = COUNTRIES.get(code)
    return names[0] if names else code


def flag(code):
    """Return the flag emoji for an ISO-3166 alpha-2 code (empty if unknown)."""
    if len(code) != 2 or not code.isalpha() or not code.isascii():
        return ""
    return "".join(chr(0x1F1E6 + ord(char) - ord("A")) for char in code.upper())


def group_title(code):
    """Bangla-first IPTV group: flag, Bangla country name, and ISO code."""
    if code == UNKNOWN_CODE:
        return f"{flag('UN')} {UNKNOWN[1]} (XX)"
    return f"{flag(code)} {country_name(code)} ({code})"


def file_stem(code):
    """Stable file name: BD_BANGLADESH.m3u, XX_UNKNOWN.m3u."""
    name = country_english_name(code) if code != UNKNOWN_CODE else "UNKNOWN"
    slug = "".join(char if char.isalnum() else "_" for char in name.upper())
    while "__" in slug:
        slug = slug.replace("__", "_")
    return f"{code}_{slug.strip('_')}"



# Traditional Bangla collation order: independent vowels, then consonants in
# the order taught at school, then dependent vowel signs. Sorting by Unicode
# code point puts many of these in the wrong place (e.g. "পো" before "পা"), so
# country names in the playlists are sorted with these weights instead.
_BANGLA_ORDER = (
    'অআইঈউঊঋএঐওঔ'
    'কখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহ'
    'ড়ঢ়য়ৎ'
    'ংঃঁ্'
    'ািীুূৃেৈোৌ'
    '০১২৩৪৫৬৭৮৯'
)
_WEIGHTS = {char: index for index, char in enumerate(_BANGLA_ORDER)}


def collation_key(text):
    """Sort key that follows Bangla letter order, keeping other text stable."""
    key = []
    for char in text.casefold():
        weight = _WEIGHTS.get(char)
        if weight is not None:
            key.append((0, weight, ord(char)))
        elif char.isascii() and char.isalnum():
            key.append((1, ord(char), ord(char)))
        else:
            key.append((2, ord(char), ord(char)))
    return tuple(key)
