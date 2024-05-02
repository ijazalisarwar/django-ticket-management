# user later
# import threading
# from django.utils.deprecation import MiddlewareMixin
# from django.contrib.auth.middleware import get_user

# _thread_locals = threading.local()


# def _do_set_current_user():
#     _thread_locals.current_user = get_user(getattr(_thread_locals, "request", None))


# class CurrentUserMiddleware(MiddlewareMixin):
#     def process_request(self, request):
#         _thread_locals.request = request
#         _do_set_current_user()


# def get_current_user():
#     return getattr(_thread_locals, "current_user", None)
