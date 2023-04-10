from django import template
from macavity.models import *

register = template.Library()

@register.inclusion_tag('macavity/tags/draw_videos.html', takes_context=True)
def draw_videos(context, context_object = None):
    if context_object is None: 
        return context
    else:
        print(context_object)
        return {
            'videos': context_object
        }