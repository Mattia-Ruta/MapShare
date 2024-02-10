from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.conf import settings
from mapshare.functions import getCountryCode3
from ipware import get_client_ip
import mapcode as mc
import reverse_geocoder as rg
import json
import ipdata
import math
import pycountry


def index(request, mapcode, context = False):
    msg = None
    initialZoom = 10
    isValidMapcode = False
    territory = context
    coords = (51.500675, -0.124578)
    
    client_ip, is_routable = get_client_ip(request)
    ipdata.api_key = settings.IPDATA_API_KEY

    if not context:
        # Check if international mapcode
        if mc.isvalid(mapcode, 0):
            response = mc.decode(mapcode)
            if math.isnan(response[0]) or math.isnan(response[1]):
                # Not a valid mapcode, might need context
                if (client_ip == "127.0.0.1"):
                    context = "GBR"
                else:
                    response = ipdata.lookup(client_ip)
                    context = getCountryCode3(response.get("country_code", "GB"))
            else:
                # International mapcode
                context = "AAA"
                coords = mc.decode(mapcode)
                territory = "International (No context needed)"
        else:
            msg = f"'{mapcode}' is an invalid mapcode"
            context = ""
            mapcode = ""
    else:
        # Context given, get coords
        if mc.isvalid(f"{context} {mapcode}"):
            coords = mc.decode(f"{context} {mapcode}")
            initialZoom = 35
            isValidMapcode = True
        else:
            msg = f"'{context} {mapcode}' is an invalid mapcode"

    if not context == "AAA":
        response = rg.get((coords[0], coords[1]))
        if response["admin1"]:
            countryInfo = pycountry.countries.get(alpha_2=response["cc"], default=context)
            territory = f"{response['admin1']}, {countryInfo.name}"

    # TODO: Add function to get territory from coordinates and add to AJAX view
    vars = {
        "msg": msg,
        "urlLat": coords[0] or 51.500675,
        "urlLng": coords[1] or -0.124578,
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
        body = json.loads(request.body)
        response = mc.encode(body["lat"], body["lng"])
        if len(response) > 0:
            payload = {"success": "true", "mapcodes": []}
            for mapcode in response:
                territory = mapcode[1]
                locationInfo = rg.get((body["lat"], body["lng"]))
                if locationInfo["cc"] == "US":
                    territory = f"{locationInfo['admin1']}, United States"
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