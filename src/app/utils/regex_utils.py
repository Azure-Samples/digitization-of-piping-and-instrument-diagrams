import re


def does_string_contain_only_one_number_or_one_fraction(string: str):
    '''Checks if a string contains only one number or one fraction

    :param string: The string to check
    :type string: str
    :return: True if the string contains only one number or one fraction, False otherwise
    :rtype: bool
    '''
    expression = r"^[\s]*([0-9]+|[0-9]+/[0-9]+)[\s]*$"
    return bool(re.search(expression, string))


def does_string_contain_at_least_one_number_and_one_letter(string: str):
    '''Checks if a string contains at least one number and one letter

    :param string: The string to check
    :type string: str
    :return: True if the string contains at least one number and one letter, False otherwise
    :rtype: bool
    '''
    expression = r"^(?=.*[a-zA-Z])(?=.*[0-9])"
    return bool(re.search(expression, string))


def is_symbol_text_invalid(string: str):
    '''Checks if the symbol text is invalid

    :param string: The string to check
    :type string: str
    :return: True if the string is invalid, False otherwise
    :rtype: bool
    '''
    # invalid expression are things like 3/4"x1/2" or 1" x 2" or 1"x2" or any other combination of numbers, spaces, and quotes
    expression_multiply_inches = r"^([0-9]+|[0-9]+/[0-9]+)[\"|%|*]*[\s]*[xX][\s]*.*([0-9]+|[0-9]+/[0-9]+)[\"|%|*]*.*$"
    if bool(re.search(expression_multiply_inches, string)):
        return True

    # invalid expression are things like 3/4" or 1" or any other combination of numbers and quotes
    expression_single_inches = r"^([0-9]+|[0-9]+/[0-9]+)[\"%*]+$"
    if bool(re.search(expression_single_inches, string)):
        return True

    return False
