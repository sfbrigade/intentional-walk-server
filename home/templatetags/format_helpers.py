from django import template

register = template.Library()

def m_to_mi(value):
    return value * 0.000621371

register.filter('m_to_mi', m_to_mi)
