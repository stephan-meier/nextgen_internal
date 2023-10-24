# -*- coding: utf-8 -*-
"""
Created on Tue Aug 15 09:34:19 2023

@author: steph
"""

# ✅ function returns new dictionary (does NOT mutate original)

def remove_nested_keys(dictionary, keys_to_remove):
    new_dict = {}

    for key, value in dictionary.items():
        if key not in keys_to_remove:
            if isinstance(value, dict):
                new_dict[key] = remove_nested_keys(value, keys_to_remove)
            else:
                new_dict[key] = value

    return new_dict


my_dict = {
    'address': {
        'country': 'Finland',
        'city': 'Oulu',
    },
    'name': 'Frank',
    'age': 30,
}

result = remove_nested_keys(my_dict, ['country', 'name'])
print(result)  # 👉️ {'address': {'city': 'Oulu'}, 'age': 30}

result = remove_nested_keys(my_dict, ['city', 'age'])
print(result)  # 👉️ {'address': {'country': 'Finland'}, 'name': 'Frank'}
