from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponseNotFound
from django.conf import settings
from mapshare.functions import getCountryCode3, isAValidMapcode
from ipware import get_client_ip
import mapcode as mc
import reverse_geocoder as rg
import json
import ipdata
import math
import pycountry
import googlemaps


def index(request, mapcode = False, context = False):
    msg = ""
    initialZoom = 10
    isValidMapcode = isAValidMapcode(context, mapcode)
    territory = context
    coords = False
    
    client_ip, is_routable = get_client_ip(request)
    if client_ip == "127.0.0.1": client_ip = "31.94.18.51"
    ipdata.api_key = settings.IPDATA_API_KEY
    lookupData = ipdata.lookup(client_ip)
    if settings.DEBUG:
        print(f"Lookup Data: {lookupData}")

    if mapcode and context and isValidMapcode:
        coords = mc.decode(mapcode, context)
    elif mapcode and context and not isValidMapcode:
        msg = f"{context} {mapcode} is an invalid mapcode."
        coords = False
        context = ""
        mapcode = ""
    elif mapcode and not context:
        context = getCountryCode3(lookupData.get("country_code", "GB"))
        mapcode = mc.encode(lookupData["latitude"], lookupData["longitude"])[0][0]
        if mc.isvalid(f"{context} {mapcode}"):
            coords = (lookupData.get("latitude", 51.5006785719964), lookupData.get("longitude", -0.12454569))
        else:
            msg = f"""
                We need a context for the mapcode {mapcode} or it is an invalid code.

                Try again with the ISO 3166 3-letter country code in the URL.
                (For example: GBR for United Kingdom, ITA for Italy, etc)
                More info at https://mapshare.xyz/about
            """
    else:
        context = getCountryCode3(lookupData.get("country_code", "GB"))
        coords = (lookupData.get("latitude", 51.5006785719964), lookupData.get("longitude", -0.12454569))
        mapcode = mc.encode(coords[0], coords[1])[0][0]
        isValidMapcode = True
        initialZoom = 35

    if coords:
        response = rg.get((coords[0], coords[1]))
        if response["admin1"]:
            countryInfo = pycountry.countries.get(alpha_2=response["cc"], default=context)
            territory = f"{response['admin1']}, {countryInfo.name}"

    # TODO: Add function to get territory from coordinates and add to AJAX view
    # TODO: Make it so you don't have to have AAA as the context for international mapcodes
    vars = {
        "msg": msg,
        "debug" : settings.DEBUG,
        "urlLat": coords[0] if coords else 51.500675,
        "urlLng": coords[1] if coords else -0.124578,
        "context": context,
        "mapcode": mapcode,
        "initialZoom": initialZoom,
        "isValidMapcode": isValidMapcode,
        "maptilerAPIKey": settings.MAPTILER_API_KEY,
        "mapboxAPIKey": settings.MAPBOX_API_KEY,
        "territory": territory,
        "googlemapsAPIKey": settings.GOOGLEMAPS_API_KEY,
        "lookupCountry": lookupData.country_name,
        "lookupCountryCode": lookupData.country_code,
        "lookupContext": getCountryCode3(lookupData.country_code),
        "lookupRegion": lookupData.region,
        "lookupCity": lookupData.city,
        "lookupLat": lookupData.latitude,
        "lookupLng": lookupData.longitude,
    }
    return render(request, "index.html", vars)


def getMapcodeAJAX(request):
    if request.method == "POST":
        body = json.loads(request.body)
        response = mc.encode(body["lat"], body["lng"])
        if len(response) > 0:
            payload = {"success": "true", "mapcodes": []}
            for elem in response:
                mapcode = elem[0]
                territory = elem[1]
                locationInfo = rg.get((body["lat"], body["lng"]))
                country = pycountry.countries.get(alpha_2=locationInfo["cc"]).name
                territory = f"{locationInfo['admin1']}, {country}"

                payload["mapcodes"].append({"context": elem[1], "mapcode": elem[0], "territory": territory or elem[1]})
            return HttpResponse(json.dumps(payload), content_type="application/json")
        else:
            return HttpResponse(json.dumps({"success": False, "error": "Invalid coordinates"}), content_type="application/json")
    else:
        return HttpResponseForbidden()

def favicon(request):
    # TODO: Add favicon file
    return HttpResponseNotFound()

def about(request):
    return render(request, "about.html")