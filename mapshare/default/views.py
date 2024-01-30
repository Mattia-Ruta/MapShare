from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.conf import settings
from mapshare.functions import getCountryCode3
from ipware import get_client_ip
import mapcode as mc
import json
import ipdata
import pycountry


def index(request, context = "GBR", mapcode = "JJ.55"):
    msg = None
    initialZoom = 10
    isValidMapcode = False
    territory = ""
    
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
        territory = pycountry.countries.get(alpha_3=context).name or "Unknown"
    elif not mapcode and not context:
        pass
    else:
        msg = f"'{context} {mapcode}' is an invalid mapcode"

    vars = {
        "msg": msg,
        "urlLat": coords[0],
        "urlLng": coords[1],
        "context": context,
        "mapcode": mapcode,
        "initialZoom": initialZoom,
        "isValidMapcode": isValidMapcode,
        "maptilerAPIKey": settings.MAPTILER_API_KEY,
        "territory": territory
    }
    return render(request, "index.html", vars)


def getMapcodeAJAX(request):
    if request.method == "POST":
        success = False
        body = json.loads(request.body)
        response = mc.encode(body["lat"], body["lng"])
        if len(response) > 0:
            payload = {"success": "true", "mapcodes": []}
            for mapcode in response:
                if mapcode[1] == "AAA":
                    territory = "International"
                else:
                    country = pycountry.countries.get(alpha_3=mapcode[1])
                    if country:
                        territory = country.name
                payload["mapcodes"].append({"context": mapcode[1], "mapcode": mapcode[0], "territory": territory or mapcode[1]})
            return HttpResponse(json.dumps(payload), content_type="application/json")
        else:
            return HttpResponse(json.dumps({"success": False}), content_type="application/json")
    else:
        return HttpResponseForbidden()