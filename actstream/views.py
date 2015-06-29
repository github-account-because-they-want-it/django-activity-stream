from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse

from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.csrf import csrf_exempt

from actstream import actions, models, compat

User = compat.get_user_model()


def respond(request, code):
    """
    Responds to the request with the given response code.
    If ``next`` is in the form, it will redirect instead.
    """
    redirect = request.GET.get('next', request.POST.get('next'))
    if redirect:
        return HttpResponseRedirect(redirect)
    return type('Response%d' % code, (HttpResponse, ), {'status_code': code})()


@login_required
@csrf_exempt
def follow_unfollow(request, content_type_id, object_id, do_follow=True, actor_only=True):
    """
    Creates or deletes the follow relationship between ``request.user`` and the
    actor defined by ``content_type_id``, ``object_id``.
    """
    ctype = get_object_or_404(ContentType, pk=content_type_id)
    instance = get_object_or_404(ctype.model_class(), pk=object_id)

    if do_follow:
        actions.follow(request.user, instance, actor_only=actor_only)
        return respond(request, 201)   # CREATED
    actions.unfollow(request.user, instance)
    return respond(request, 204)   # NO CONTENT


@login_required
def stream(request):
    """
    Index page for authenticated user's activity stream. (Eg: Your feed at
    github.com)
    """
    return render_to_response('actstream/actor.html', {
        'ctype': ContentType.objects.get_for_model(User),
        'actor': request.user, 'action_list': models.user_stream(request.user)
    }, context_instance=RequestContext(request))


def followers(request, content_type_id, object_id):
    """
    Creates a listing of ``User``s that follow the actor defined by
    ``content_type_id``, ``object_id``.
    """
    ctype = get_object_or_404(ContentType, pk=content_type_id)
    instance = get_object_or_404(ctype.model_class(), pk=object_id)
    return render_to_response('actstream/followers.html', {
        'followers': models.followers(instance), 'actor': instance
    }, context_instance=RequestContext(request))


def following(request, user_id):
    """
    Returns a list of actors that the user identified by ``user_id`` is following (eg who im following).
    """
    instance = get_object_or_404(User, pk=user_id)
    return render_to_response('actstream/following.html', {
        'following': models.following(instance), 'user': instance
    }, context_instance=RequestContext(request))


def user(request, username):
    """
    ``User`` focused activity stream. (Eg: Profile page twitter.com/justquick)
    """
    instance = get_object_or_404(User, **{'is_active': True, compat.username_field(): username})
    return render_to_response('actstream/actor.html', {
        'ctype': ContentType.objects.get_for_model(User),
        'actor': instance, 'action_list': models.user_stream(instance)
    }, context_instance=RequestContext(request))


def detail(request, action_id):
    """
    ``Action`` detail view (pretty boring, mainly used for get_absolute_url)
    """
    return render_to_response('actstream/detail.html', {
        'action': get_object_or_404(models.Action, pk=action_id)
    }, context_instance=RequestContext(request))


def actor(request, content_type_id, object_id):
    """
    ``Actor`` focused activity stream for actor defined by ``content_type_id``,
    ``object_id``.
    """
    ctype = get_object_or_404(ContentType, pk=content_type_id)
    instance = get_object_or_404(ctype.model_class(), pk=object_id)
    return render_to_response('actstream/actor.html', {
        'action_list': models.actor_stream(instance), 'actor': instance,
        'ctype': ctype
    }, context_instance=RequestContext(request))


def model(request, content_type_id):
    """
    ``Actor`` focused activity stream for actor defined by ``content_type_id``,
    ``object_id``.
    """
    ctype = get_object_or_404(ContentType, pk=content_type_id)
    model_class = ctype.model_class()
    return render_to_response('actstream/actor.html', {
        'action_list': models.model_stream(model_class), 'ctype': ctype,
        'actor': model_class
    }, context_instance=RequestContext(request))


def mark_seen(request):
    if request.method != "PUT":
        return HttpResponse(status=400)
    models.Action.objects.filter(id__in=request.PUT["ids"]).update(seen=True)
    return HttpResponse(status=200)
