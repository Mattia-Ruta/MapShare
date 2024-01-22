from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.conf import settings
from mapshare.functions import getCountryCode3
from ipware import get_client_ip
import mapcode as mc
import json
import ipdata


def index(request, context="", mapcode=""):
    msg = None
    initialZoom = 10
    isValidMapcode = False
    
    client_ip, is_routable = get_client_ip(request)
    ipdata.api_key = settings.IPDATA_API_KEY

    # Get starting area and context
    if client_ip is None or client_ip == "127.0.0.1":
        context = "GBR"
        coords = (51.500675,-0.124578)
    else:
        response = ipdata.lookup(client_ip)
        context = getCountryCode3(response.get("country_code", "GB"))
        coords = (response.get("latitude", 51.500675),response.get("longitude", -0.124578))

    if mc.isvalid(f"{context} {mapcode}"):
        coords = mc.decode(f"{context} {mapcode}")
        initialZoom = 40
        isValidMapcode = True
    elif len(mapcode) == 0 and len(context) == 0:
        pass
    else:
        msg = f"'{context} {mapcode}' is an invalid mapcode"

    context = {
        "msg": msg,
        "urlLat": coords[0],
        "urlLng": coords[1],
        "context": context,
        "mapcode": mapcode,
        "initialZoom": initialZoom,
        "isValidMapcode": isValidMapcode,
        "maptilerAPIKey": settings.MAPTILER_API_KEY
    }
    return render(request, "index.html", context)


def getMapcodeAJAX(request):
    if request.method == "POST":
        success = False
        body = json.loads(request.body)
        response = mc.encode(body["lat"], body["lng"])
        if len(response) > 0:
            payload = [("success", "true")]
            for mapcode in response:
                payload.append((mapcode[1], mapcode[0]))
            payload = dict(payload)
            return HttpResponse(json.dumps(payload), content_type="application/json")
        else:
            return HttpResponse(json.dumps({"success": False}), content_type="application/json")
    else:
        return HttpResponseForbidden()