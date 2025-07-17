import json
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def jsonify(value):
    """Convert a Python object to JSON string for JavaScript"""
    return mark_safe(json.dumps(value))