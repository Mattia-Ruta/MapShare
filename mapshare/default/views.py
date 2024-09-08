from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponseNotFound
from django.conf import settings
from mapshare.functions import getCountries2, getCountryCode3, isAValidMapcode
from ipware import get_client_ip
import mapcode as mc
import reverse_geocoder as rg
import json
import ipdata
import pycountry
import math
import flag


def index(request, mapcode = False, context = False):
    msg = ""
    error = ""
    initialZoom = 10
    isValidMapcode = isAValidMapcode(context, mapcode)
    if context == "AAA":
        context = False
    territory = context
    coords = False
    countryFlag = False
    
    bigBenCoords = {"lat": 51.5006785719964, "lng": -0.12454569}
    bigBenContext = "GBR"
    bigBenMapcode = "JJ.66"
    bigBenCountryFlag = "🇬🇧"
    bigBenTerritory = "England, United Kingdom"
    
    client_ip, is_routable = get_client_ip(request)
    if client_ip == "127.0.0.1": client_ip = "31.94.18.51"
    ipdata.api_key = settings.IPDATA_API_KEY
    lookupData = ipdata.lookup(client_ip)

    # Fresh Request
    if not mapcode and not context:
        if lookupData:
            print("Fresh request, generating mapcode from general location/lookup")
            coords = {"lat": lookupData["latitude"], "lng": lookupData["longitude"]}
            response = mc.encode(coords["lat"], coords["lng"])
            mapcode = response[0][0]
            context = response[0][1]
            response = rg.get((coords["lat"], coords["lng"]))
            if response["admin1"]:
                countryInfo = pycountry.countries.get(alpha_2=response["cc"], default=context)
                territory = f"{response['admin1']}, {countryInfo.name}"
                countryFlag = countryInfo.flag
            context = getCountryCode3(lookupData["country_code"])
            msg = "Mapcode generated from your general area"
        else:
            print("Could not determine general location--no location data")
            coords = bigBenCoords
            context = bigBenContext
            mapcode = bigBenMapcode
            countryFlag = bigBenCountryFlag
            territory = bigBenTerritory
            error = "Could not determine general location, here's Big Ben"
    elif mapcode and not context:
        print("Just mapcode given, checking if international context...")
        if not math.isnan(mc.decode(mapcode, "AAA")[0]):
            print(f"International Context for mapcode {mapcode}")
            context = "AAA"
            coords = mc.decode(mapcode, context)
            coords = {"lat": coords[0], "lng": coords[1]}
            betterMapcode = mc.encode(coords["lat"], coords["lng"])[0]
            msg = f"The given mapcode is using the international context, try using mapcode {betterMapcode[1]} {betterMapcode[0]} instead!"
            countryFlag = "🌐"
            territory = "International"
        else:
            # Use context from request location
            contextCheck = getCountryCode3(lookupData["country_code"])
            if mc.isvalid(f"{contextCheck} {mapcode}"):
                print(f"Not international, use context from locationData")
                coords = mc.decode(mapcode, contextCheck)
                coords = {"lat": coords[0], "lng": coords[1]}
                context = contextCheck
                countryFlag = lookupData["emoji_flag"]
                response = rg.get((coords["lat"], coords["lng"]))
                if response["admin1"]:
                    countryInfo = pycountry.countries.get(alpha_2=response["cc"], default=context)
                    territory = f"{response['admin1']}, {countryInfo.name}"
                msg = f"Used context {context} for mapcode {mapcode}"
            else:
                print("Invalid mapcode")
                error = f"{mapcode} is not a valid mapcode, try again by providing a context (ex: https://mapshare.xyz/GBR/JJ.66)"
                coords = bigBenCoords
                context = bigBenContext
                mapcode = bigBenMapcode
                countryFlag = bigBenCountryFlag
                territory = bigBenTerritory
    elif mapcode and context and isValidMapcode:
        print(f"Mapcode {context} {mapcode} is valid")
        coords = mc.decode(mapcode, context)
        coords = {"lat": coords[0], "lng": coords[1]}
        response = rg.get((coords["lat"], coords["lng"]))
        if response["admin1"]:
            countryInfo = pycountry.countries.get(alpha_2=response["cc"], default=context)
            territory = f"{response['admin1']}, {countryInfo.name}"
            countryFlag = flag.flag(response["cc"])

    altMapcodes = []
    altMapcodeTerritory = ""
    mcResponse = mc.encode(coords["lat"], coords["lng"])
    if mcResponse:
        for altMapcode in mcResponse:
            if altMapcode[1] == "AAA":
                altMapcodeTerritory = "International"
                thisCountryFlag = "🌐"
            else:
                response = rg.get((coords["lat"], coords["lng"]))
                if response["admin1"]:
                    countryInfo = pycountry.countries.get(alpha_2=response["cc"], default=context)
                    altMapcodeTerritory = f"{response['admin1']}, {countryInfo.name}"
                    thisCountryFlag = countryInfo.flag
            altMapcodes.append({"context": altMapcode[1], "mapcode": altMapcode[0], "territory": altMapcodeTerritory, "countryFlag": thisCountryFlag})

    vars = {
        "msg": msg,
        "error": error,
        "debug" : settings.DEBUG,
        "urlLat": coords["lat"] if coords else 51.500675,
        "urlLng": coords["lng"] if coords else -0.124578,
        "context": context,
        "mapcode": mapcode,
        "altMapcodes": altMapcodes,
        "initialZoom": initialZoom,
        "isValidMapcode": isValidMapcode,
        "maptilerAPIKey": settings.MAPTILER_API_KEY,
        "mapboxAPIKey": settings.MAPBOX_API_KEY,
        "googleMapsKey": settings.GOOGLEMAPS_API_KEY,
        "territory": territory,
        "googlemapsAPIKey": settings.GOOGLEMAPS_API_KEY,
        "lookupCountry": lookupData.country_name,
        "lookupCountryCode": lookupData.country_code,
        "lookupContext": getCountryCode3(lookupData.country_code),
        "lookupRegion": lookupData.region,
        "lookupCity": lookupData.city,
        "lookupLat": lookupData.latitude,
        "lookupLng": lookupData.longitude,
        "countries2": getCountries2(),
        "countryFlag": countryFlag,
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
                context = elem[1]

                locationInfo = rg.get((body["lat"], body["lng"]))
                if context == "AAA":
                    territory = "International"
                    countryFlag = "🌐"
                else:
                    country = pycountry.countries.get(alpha_2=locationInfo["cc"])
                    territory = f"{locationInfo['admin1']}, {country.name}"
                    countryFlag = country.flag

                payload["mapcodes"].append({
                    "context": context,
                    "mapcode": mapcode,
                    "territory": territory or elem[1],
                    "countryFlag": countryFlag,
                })
            return HttpResponse(json.dumps(payload), content_type="application/json")
        else:
            return HttpResponse(json.dumps({"success": False, "error": "Invalid coordinates"}), content_type="application/json")
    else:
        return HttpResponseForbidden()

def getCountryFromCountry2AJAX(request):
    if request.method =="POST":
        body = json.loads(request.body)
        print(body)
    else:
        return HttpResponseForbidden()

def favicon(request):
    # TODO: Add favicon file
    return HttpResponseNotFound()

def about(request):
    return render(request, "about.html")
