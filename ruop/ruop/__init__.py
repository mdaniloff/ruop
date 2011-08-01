from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from ruop.models import initialize_sql

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    initialize_sql(engine)
    config = Configurator(settings=settings)
    config.add_static_view('static', 'ruop:static')
    config.add_route('home', '/')
    config.add_route('details', '/details')
    config.add_route('details_reference', '/details/{reference}')

    config.add_view('ruop.views.my_view',
                    route_name='home',
                    renderer='templates/mytemplate.pt')
    config.add_view('ruop.views.details',
                    route_name='details',
                    renderer='templates/details.pt')
    config.add_view('ruop.views.details_reference',
                    route_name='details_reference',
                    renderer='templates/details_reference.pt')
    return config.make_wsgi_app()

