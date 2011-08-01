from ruop.models import DBSession
import sqlalchemy as sa

def my_view(request):
    
    dbsession = DBSession()
    result = dbsession.execute(sa.text("select reference, name from app_measure "))

    return {'project':'ruop', 'result':result}


from pyramid.view import view_config
@view_config(route_name="details", renderer="templates/details.pt")
def details(request):
    
    dbsession = DBSession()
    result = dbsession.execute(sa.text("select name, purpose from app_measure --where reference =%s "))

    return {'project':'ruop', 'result': result}

@view_config(route_name="details_reference", renderer="templates/details_reference.pt")
def details_reference(request, reference):
    
    dbsession = DBSession()
    result = dbsession.execute(sa.text("select name, purpose from app_measure --where reference =%s "))
    print "THIS IS A REFERENCE --> " +str(reference)
    return {'project':'ruop', 'result': result, 'reference': reference}
